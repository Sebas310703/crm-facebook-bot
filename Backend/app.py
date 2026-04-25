"""
app.py — CRM PolitiCRM
Versión definitiva integrada.

Combina:
  - Backend/ (versión inicial)
  - app.py raíz (versión avanzada con nurturing, comentarios, WhatsApp)

Nuevos endpoints:
  - /emails/send-pending         ← faltaba en raíz
  - /lideres/                    ← CRUD líderes (lideres_seguros)
  - /lideres/{id}/encolar        ← encola nurturing para un líder
  - /barrios/                    ← listado de barrios
  - /nurturing/sequences         ← ver secuencias configuradas
"""

import os
import re
import logging
from datetime import datetime

from fastapi import FastAPI, Depends, Request, HTTPException, Body, BackgroundTasks, Query
from fastapi.responses import PlainTextResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import func

# ── Internos ──────────────────────────────────────────────
from database import SessionLocal, engine, get_db
from models import (
    Base,
    Contact,
    Event,
    EmailTemplate,
    EmailQueue,
    ConversationState,
)
from automation import run_automation
from email_sender import send_pending_emails
from facebook_api import send_facebook_message, send_facebook_private_reply

# ── Nurturing ─────────────────────────────────────────────
from nurturing_models import Base as NurturingBase, NurturingLog, NurturingSequence
from nurturing_engine import start_scheduler, enqueue_contact, process_pending

# ── Líderes ───────────────────────────────────────────────
from lider_model import LiderSeguro, Barrio

# ── Logging ───────────────────────────────────────────────
logging.basicConfig(level=logging.INFO, format="%(asctime)s [APP] %(message)s")
logger = logging.getLogger(__name__)

# =========================================================
# CONFIGURACIÓN
# =========================================================

FACEBOOK_VERIFY_TOKEN = os.getenv("FACEBOOK_VERIFY_TOKEN", "mi_token_de_prueba")
CANDIDATO = os.getenv("CANDIDATO_NOMBRE", "Carlos Julio Socha")

ENGAGEMENT_SCORE_MAP = {
    "FB_LIKE": 1,
    "FB_COMMENT": 3,
    "FB_SHARE": 5,
    "FB_MESSAGE": 4,
    "FORM_COMPLETED": 6,
}

COMMENT_KEYWORDS = {
    "INFO": {
        "reply": (
            "👋 ¡Gracias por comentar INFO!\n\n"
            "Te escribo por aquí para ayudarte rápido.\n"
            "¿Te interesa información general o hablar con un asesor?"
        ),
        "topic": "info",
    },
    "PRECIO": {
        "reply": (
            "💰 ¡Listo! Sobre precios: manejamos opciones según lo que necesites.\n\n"
            "Para darte un rango, ¿qué estás buscando exactamente?"
        ),
        "topic": "precio",
    },
    "ASESOR": {
        "reply": (
            "🙋 Perfecto. Te conecto con un asesor.\n\n"
            "¿Me confirmas tu nombre y tu WhatsApp (empieza por 3)?"
        ),
        "topic": "asesor",
    },
}

# =========================================================
# PYDANTIC SCHEMAS
# =========================================================


class ContactInfo(BaseModel):
    user_id: str
    full_name: str | None = None
    email: str | None = None
    phone: str | None = None


class MessengerInput(BaseModel):
    user_id: str
    text: str


class LiderCreate(BaseModel):
    nombre: str
    telefono: str | None = None
    direccion: str | None = None
    barrio_id: int


class WhatsAppMasivoInput(BaseModel):
    mensaje: str | None = None
    template_name: str | None = None
    barrio_id: int | None = None
    limite: int | None = None


# =========================================================
# APP + MIDDLEWARES
# =========================================================

# Crear tablas
Base.metadata.create_all(bind=engine)
NurturingBase.metadata.create_all(bind=engine)

app = FastAPI(
    title="PolitiCRM API",
    description="CRM político con nurturing WhatsApp, Facebook Messenger y email.",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # Ajustar en producción
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    start_scheduler()
    logger.info("✓ PolitiCRM API iniciada")


# =========================================================
# HELPERS DE NEGOCIO
# =========================================================


def get_or_create_contact(
    db: Session,
    external_id: str,
    default_name: str | None = None,
) -> Contact:
    contact = db.query(Contact).filter_by(external_id=external_id).first()
    if not contact:
        contact = Contact(
            external_id=external_id,
            full_name=default_name or "Usuario Facebook",
        )
        db.add(contact)
        db.commit()
        db.refresh(contact)
    return contact


def get_or_create_conversation_state(
    db: Session,
    contact: Contact,
    channel: str = "messenger",
) -> ConversationState:
    state = (
        db.query(ConversationState)
        .filter_by(contact_id=contact.id, channel=channel)
        .first()
    )
    if not state:
        state = ConversationState(
            contact_id=contact.id,
            channel=channel,
            step="start",
        )
        db.add(state)
        db.commit()
        db.refresh(state)
    return state


def update_segment_by_score(contact: Contact) -> None:
    score = contact.engagement_score or 0
    if score >= 40:
        contact.segment = "muy_activo"
    elif score >= 15:
        contact.segment = "interesado"
    elif score > 0:
        contact.segment = "curioso"
    else:
        contact.segment = "inactivo"


def is_valid_email(email: str) -> bool:
    return bool(re.match(r"^[\w\.-]+@[\w\.-]+\.\w+$", email))


def is_valid_colombian_phone(phone: str) -> bool:
    return phone.isdigit() and phone.startswith("3") and len(phone) == 10


def register_event(
    db: Session,
    contact: Contact,
    event_type: str,
    topic: str | None = None,
    text: str | None = None,
    update_engagement: bool = True,
) -> Event:
    event = Event(
        contact_id=contact.id,
        event_type=event_type,
        topic=topic,
        text=text,
    )
    db.add(event)

    if update_engagement:
        if topic and not contact.main_topic:
            contact.main_topic = topic
        contact.engagement_score = (contact.engagement_score or 0) + ENGAGEMENT_SCORE_MAP.get(event_type, 0)
        contact.last_interaction = datetime.utcnow()
        update_segment_by_score(contact)

    return event


# =========================================================
# HELPERS COMENTARIOS FACEBOOK
# =========================================================


def _comment_topic(comment_id: str) -> str:
    return f"comment_id:{comment_id}"


def already_processed_comment(db: Session, comment_id: str) -> bool:
    marker = _comment_topic(comment_id)
    return (
        db.query(Event)
        .filter(
            Event.topic == marker,
            Event.event_type.in_(["FB_COMMENT", "FB_PRIVATE_REPLY_SENT"]),
        )
        .first()
    ) is not None


def detect_keyword(comment_text: str) -> str | None:
    if not comment_text:
        return None
    t = comment_text.strip().upper()
    for kw in COMMENT_KEYWORDS:
        if t == kw or kw in t:
            return kw
    return None


def process_facebook_comment(
    db: Session,
    comment_id: str,
    from_id: str,
    from_name: str | None,
    post_id: str | None,
    comment_text: str | None,
) -> None:
    if not comment_id or not from_id:
        return
    if already_processed_comment(db, comment_id):
        return

    contact = get_or_create_contact(
        db,
        external_id=f"fb_user:{from_id}",
        default_name=from_name or "Usuario Facebook",
    )

    register_event(
        db=db,
        contact=contact,
        event_type="FB_COMMENT",
        topic=_comment_topic(comment_id),
        text=(comment_text or "").strip()[:1000],
        update_engagement=True,
    )

    kw = detect_keyword(comment_text or "")
    if kw:
        reply_text = COMMENT_KEYWORDS[kw]["reply"]
        if not contact.main_topic:
            contact.main_topic = COMMENT_KEYWORDS[kw]["topic"]
    else:
        reply_text = (
            "👋 ¡Gracias por tu comentario!\n"
            "Te escribo por aquí para ayudarte.\n\n"
            "Escribe: INFO, PRECIO o ASESOR 🙌"
        )

    db.commit()

    ok = send_facebook_private_reply(comment_id, reply_text)

    register_event(
        db=db,
        contact=contact,
        event_type="FB_PRIVATE_REPLY_SENT" if ok else "FB_PRIVATE_REPLY_FAILED",
        topic=_comment_topic(comment_id),
        text=f"post_id={post_id or 'N/A'}",
        update_engagement=False,
    )
    db.commit()


# =========================================================
# RUTAS BÁSICAS
# =========================================================


@app.get("/", tags=["General"])
def read_root():
    return {
        "message": "PolitiCRM API funcionando 🚀",
        "version": "2.0.0",
        "candidato": CANDIDATO,
        "docs": "/docs",
    }


# =========================================================
# WEBHOOK FACEBOOK
# =========================================================


@app.get("/webhook/facebook", tags=["Facebook"])
async def verify_facebook_webhook(request: Request):
    """Verificación del webhook por parte de Meta."""
    mode = request.query_params.get("hub.mode")
    token = request.query_params.get("hub.verify_token")
    challenge = request.query_params.get("hub.challenge")

    if mode == "subscribe" and token == FACEBOOK_VERIFY_TOKEN:
        return PlainTextResponse(challenge)
    raise HTTPException(status_code=403, detail="Verification failed")


@app.post("/webhook/facebook", tags=["Facebook"])
async def facebook_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    body: dict = Body(...),
    db: Session = Depends(get_db),
):
    """Recibe eventos reales de Facebook (Messenger + comentarios de posts)."""
    logger.info("[FB] Webhook recibido")

    for entry in body.get("entry", []):

        # ── MENSAJES MESSENGER ────────────────────────────
        for event in entry.get("messaging", []):
            psid = event.get("sender", {}).get("id")
            message = event.get("message")
            if not message or not psid:
                continue

            text = message.get("text")
            if not text:
                continue

            user_text = text.strip()
            contact = get_or_create_contact(db, external_id=psid)
            register_event(db, contact, "FB_MESSAGE", contact.main_topic or "general", user_text)

            state = get_or_create_conversation_state(db, contact)
            reply = _bot_step(db, contact, state, user_text, background_tasks, via="webhook")

            state.last_message = user_text
            state.updated_at = datetime.utcnow()
            db.commit()

            if reply:
                send_facebook_message(psid, reply)

        # ── COMENTARIOS DE POSTS ──────────────────────────
        for change in entry.get("changes", []):
            if change.get("field") != "feed":
                continue
            value = change.get("value", {}) or {}
            if value.get("item") != "comment" or value.get("verb") != "add":
                continue

            process_facebook_comment(
                db=db,
                comment_id=value.get("comment_id"),
                from_id=(value.get("from") or {}).get("id"),
                from_name=(value.get("from") or {}).get("name"),
                post_id=value.get("post_id"),
                comment_text=value.get("message") or "",
            )

    return {"status": "ok"}


# ── Máquina de estados del bot (reutilizable) ─────────────

def _bot_step(
    db: Session,
    contact: Contact,
    state: ConversationState,
    user_text: str,
    background_tasks: BackgroundTasks,
    via: str = "webhook",
) -> str:
    reply = ""

    if state.step == "start":
        reply = (
            f"👋 Hola, soy el asistente de la campaña de {CANDIDATO}.\n"
            "¿Te gustaría recibir más información por correo y WhatsApp?\n"
            "Por favor, responde con tu correo electrónico."
        )
        state.step = "ask_email"

    elif state.step == "ask_email":
        if not is_valid_email(user_text):
            reply = (
                "❌ El correo que escribiste no es válido.\n"
                "Por favor escribe un correo correcto (ej: nombre@gmail.com)."
            )
        else:
            contact.email = user_text
            state.step = "ask_phone"
            reply = (
                "✅ Correo guardado correctamente.\n"
                "Ahora escribe tu número de WhatsApp (10 dígitos, empieza por 3)."
            )

    elif state.step == "ask_phone":
        if not is_valid_colombian_phone(user_text):
            reply = (
                "❌ Ese número no es válido.\n"
                "Debe tener 10 dígitos y empezar por 3.\n"
                "Ejemplo: 3001234567"
            )
        else:
            contact.phone = user_text
            state.step = "completed"
            reply = (
                "✅ ¡Perfecto! Tus datos han sido registrados correctamente.\n"
                "Muy pronto te enviaremos información personalizada."
            )
            register_event(
                db, contact,
                "FORM_COMPLETED",
                contact.main_topic or "general",
                f"Formulario completado vía Messenger ({via})",
            )
            # Encolar secuencia nurturing en background
            telefono_e164 = f"+57{user_text}"
            background_tasks.add_task(
                enqueue_contact,
                db=SessionLocal(),
                contact_id=contact.id,
                contact_type="contact",
                nombre=contact.full_name or "Líder",
                telefono=telefono_e164,
                sector=contact.main_topic,
            )

    elif state.step == "completed":
        reply = (
            "Ya tengo tus datos registrados 🙌.\n"
            "Si tienes alguna pregunta, puedes escribirla."
        )

    return reply


# =========================================================
# MESSENGER SIMULATE
# =========================================================


@app.post("/messenger/simulate", tags=["Facebook"])
def messenger_simulate(
    data: MessengerInput,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """Simula conversación con el bot sin necesidad del webhook real."""
    contact = get_or_create_contact(db, external_id=data.user_id)
    user_text = data.text.strip()

    register_event(db, contact, "FB_MESSAGE", contact.main_topic or "general", user_text)
    state = get_or_create_conversation_state(db, contact)
    reply = _bot_step(db, contact, state, user_text, background_tasks, via="simulate")

    state.last_message = user_text
    state.updated_at = datetime.utcnow()
    db.commit()

    return {
        "status": "ok",
        "bot_reply": reply,
        "conversation_step": state.step,
        "contact": {
            "id": contact.id,
            "email": contact.email,
            "phone": contact.phone,
            "segment": contact.segment,
            "engagement_score": contact.engagement_score,
        },
    }


# =========================================================
# CONTACTOS / EVENTOS
# =========================================================


@app.post("/contact/update-info", tags=["Contactos"])
def update_contact_info(data: ContactInfo, db: Session = Depends(get_db)):
    """Actualiza datos de un contacto existente o lo crea."""
    contact = get_or_create_contact(db, external_id=data.user_id)
    if data.full_name:
        contact.full_name = data.full_name
    if data.email:
        contact.email = data.email
    if data.phone:
        contact.phone = data.phone
    db.commit()
    db.refresh(contact)
    return {
        "status": "ok",
        "contact_id": contact.id,
        "full_name": contact.full_name,
        "email": contact.email,
        "phone": contact.phone,
    }


@app.post("/facebook/event", tags=["Contactos"])
def receive_event(data: dict, db: Session = Depends(get_db)):
    """Registra un evento de Facebook (like, comentario, share, etc.)."""
    contact = get_or_create_contact(
        db,
        external_id=data["user_id"],
        default_name="Usuario Facebook",
    )
    register_event(
        db=db,
        contact=contact,
        event_type=data["type"],
        topic=data.get("topic"),
        text=data.get("text"),
    )
    db.commit()
    return {
        "status": "evento registrado",
        "contact_id": contact.id,
        "segmento": contact.segment,
        "score": contact.engagement_score,
    }


# =========================================================
# LÍDERES
# =========================================================


@app.get("/lideres/", tags=["Líderes"])
def listar_lideres(
    barrio_id: int | None = Query(None),
    activo: bool = Query(True),
    skip: int = Query(0),
    limit: int = Query(50),
    db: Session = Depends(get_db),
):
    """Lista líderes con filtros opcionales por barrio y estado activo."""
    query = db.query(LiderSeguro).filter(LiderSeguro.activo == activo)
    if barrio_id:
        query = query.filter(LiderSeguro.barrio_id == barrio_id)
    total = query.count()
    lideres = query.offset(skip).limit(limit).all()
    return {
        "total": total,
        "skip": skip,
        "limit": limit,
        "lideres": [
            {
                "id": l.id,
                "nombre": l.nombre,
                "telefono": l.telefono,
                "direccion": l.direccion,
                "barrio_id": l.barrio_id,
                "activo": l.activo,
            }
            for l in lideres
        ],
    }


@app.get("/lideres/{lider_id}", tags=["Líderes"])
def obtener_lider(lider_id: int, db: Session = Depends(get_db)):
    """Obtiene un líder por ID."""
    lider = db.get(LiderSeguro, lider_id)
    if not lider:
        raise HTTPException(status_code=404, detail="Líder no encontrado")
    return lider


@app.post("/lideres/", tags=["Líderes"])
def crear_lider(
    data: LiderCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """Crea un nuevo líder y encola su secuencia de nurturing."""
    barrio = db.get(Barrio, data.barrio_id)
    if not barrio:
        raise HTTPException(status_code=404, detail="Barrio no encontrado")

    lider = LiderSeguro(
        nombre=data.nombre,
        telefono=data.telefono,
        direccion=data.direccion,
        barrio_id=data.barrio_id,
    )
    db.add(lider)
    db.commit()
    db.refresh(lider)

    # Encolar nurturing si tiene teléfono
    if lider.telefono:
        telefono_e164 = lider.telefono_e164()
        background_tasks.add_task(
            enqueue_contact,
            db=SessionLocal(),
            contact_id=lider.id,
            contact_type="lider",
            nombre=lider.nombre,
            telefono=telefono_e164,
            sector=barrio.nombre,
        )

    return {"status": "ok", "lider_id": lider.id, "nombre": lider.nombre}


@app.patch("/lideres/{lider_id}", tags=["Líderes"])
def actualizar_lider(
    lider_id: int,
    data: dict = Body(...),
    db: Session = Depends(get_db),
):
    """Actualiza campos de un líder (nombre, telefono, direccion, activo)."""
    lider = db.get(LiderSeguro, lider_id)
    if not lider:
        raise HTTPException(status_code=404, detail="Líder no encontrado")

    campos_permitidos = {"nombre", "telefono", "direccion", "activo"}
    for campo, valor in data.items():
        if campo in campos_permitidos:
            setattr(lider, campo, valor)

    lider.updated_at = datetime.utcnow()
    db.commit()
    return {"status": "ok", "lider_id": lider_id}


@app.post("/lideres/{lider_id}/encolar", tags=["Líderes"])
def encolar_lider(lider_id: int, db: Session = Depends(get_db)):
    """Encola manualmente la secuencia de nurturing para un líder específico."""
    lider = db.get(LiderSeguro, lider_id)
    if not lider:
        raise HTTPException(status_code=404, detail="Líder no encontrado")
    if not lider.telefono:
        raise HTTPException(status_code=400, detail="El líder no tiene teléfono registrado")

    barrio = db.get(Barrio, lider.barrio_id)
    n = enqueue_contact(
        db=db,
        contact_id=lider.id,
        contact_type="lider",
        nombre=lider.nombre,
        telefono=lider.telefono_e164(),
        sector=barrio.nombre if barrio else None,
    )
    return {"status": "ok", "mensajes_encolados": n}


# =========================================================
# BARRIOS
# =========================================================


@app.get("/barrios/", tags=["Barrios"])
def listar_barrios(db: Session = Depends(get_db)):
    """Lista todos los barrios con conteo de líderes."""
    barrios = db.query(Barrio).order_by(Barrio.nombre).all()
    return [
        {
            "id": b.id,
            "nombre": b.nombre,
            "total_lideres": db.query(LiderSeguro)
                .filter_by(barrio_id=b.id, activo=True)
                .count(),
        }
        for b in barrios
    ]


# =========================================================
# PLANTILLAS EMAIL
# =========================================================


@app.post("/init-templates", tags=["Email"])
def init_templates(db: Session = Depends(get_db)):
    """Crea plantillas básicas de email si no existen."""
    templates_data = [
        {
            "name": "bienvenida",
            "subject": "¡Bienvenido a la campaña!",
            "body": f"Gracias por unirte al proyecto de {CANDIDATO}.",
        },
        {
            "name": "reenganche",
            "subject": "Te extrañamos",
            "body": "Hace varios días que no interactúas. Tenemos nuevo contenido para ti.",
        },
        {
            "name": "profundizacion_educacion",
            "subject": "Propuestas de educación",
            "body": "Vimos que te interesa la educación. Aquí más detalles.",
        },
    ]
    creadas = 0
    for t in templates_data:
        if not db.query(EmailTemplate).filter_by(name=t["name"]).first():
            db.add(EmailTemplate(name=t["name"], subject=t["subject"], body=t["body"]))
            creadas += 1
    db.commit()
    return {"status": "ok", "templates_creadas": creadas}


# =========================================================
# AUTOMATIZACIÓN Y EMAILS
# =========================================================


@app.post("/automation/run", tags=["Automatización"])
def run_automation_endpoint(db: Session = Depends(get_db)):
    """Ejecuta el motor de automatización de emails."""
    run_automation(db)
    pendientes = db.query(EmailQueue).filter_by(status="PENDING").count()
    return {"status": "automation_ejecutada", "emails_pendientes": pendientes}


@app.get("/emails/pending", tags=["Email"])
def get_pending_emails(db: Session = Depends(get_db)):
    """Lista los emails pendientes de envío."""
    emails = db.query(EmailQueue).filter_by(status="PENDING").all()
    return [
        {
            "id": e.id,
            "contact_id": e.contact_id,
            "template_id": e.template_id,
            "scheduled_at": e.scheduled_at,
        }
        for e in emails
    ]


@app.post("/emails/send-pending", tags=["Email"])
def send_emails_endpoint(db: Session = Depends(get_db)):
    """Envía todos los emails en estado PENDING."""
    enviados = send_pending_emails(db)
    return {"status": "ok", "emails_enviados": enviados}


# =========================================================
# WHATSAPP MASIVO
# =========================================================


@app.post("/whatsapp/enviar-masivo", tags=["WhatsApp"])
def whatsapp_masivo(
    data: WhatsAppMasivoInput,
    db: Session = Depends(get_db),
):
    """Envía mensajes masivos de WhatsApp a líderes."""
    from whatsapp_sender import enviar_masivo_whatsapp

    sector = None
    if data.barrio_id:
        barrio = db.get(Barrio, data.barrio_id)
        if not barrio:
            raise HTTPException(status_code=404, detail="Barrio no encontrado")
        sector = barrio.nombre

    resumen = enviar_masivo_whatsapp(
        db=db,
        mensaje=data.mensaje,
        template_name=data.template_name,
        sector=sector,
        limite=data.limite,
    )
    return resumen


# =========================================================
# NURTURING — ADMINISTRACIÓN
# =========================================================


@app.get("/nurturing/stats", tags=["Nurturing"])
def nurturing_stats(db: Session = Depends(get_db)):
    """Resumen del estado de todos los mensajes programados."""
    stats = (
        db.query(NurturingLog.status, func.count(NurturingLog.id))
        .group_by(NurturingLog.status)
        .all()
    )
    return {status: count for status, count in stats}


@app.get("/nurturing/sequences", tags=["Nurturing"])
def listar_sequences(db: Session = Depends(get_db)):
    """Lista todas las secuencias de nurturing configuradas."""
    seqs = db.query(NurturingSequence).order_by(
        NurturingSequence.sector, NurturingSequence.dia, NurturingSequence.orden
    ).all()
    return [
        {
            "id": s.id,
            "sector": s.sector or "GLOBAL",
            "canal": s.canal,
            "dia": s.dia,
            "orden": s.orden,
            "activo": s.activo,
            "mensaje_preview": s.mensaje[:80] + "..." if len(s.mensaje) > 80 else s.mensaje,
        }
        for s in seqs
    ]


@app.post("/nurturing/encolar-lideres", tags=["Nurturing"])
def encolar_lideres_existentes():
    """
    Encola la secuencia completa para todos los líderes existentes.
    Ejecutar UNA sola vez desde /docs.
    """
    from nurturing_engine import enqueue_lideres_existentes
    total = enqueue_lideres_existentes()
    return {"mensajes_programados": total}


@app.post("/nurturing/procesar-ahora", tags=["Nurturing"])
def procesar_ahora(batch_size: int = Query(5)):
    """Fuerza el envío inmediato de mensajes pendientes. Útil para pruebas."""
    return process_pending(batch_size=batch_size)


# =========================================================
# DASHBOARD RÁPIDO
# =========================================================


@app.get("/dashboard/resumen", tags=["Dashboard"])
def dashboard_resumen(db: Session = Depends(get_db)):
    """Resumen general del CRM para el dashboard."""
    return {
        "lideres": {
            "total": db.query(LiderSeguro).filter_by(activo=True).count(),
            "sin_telefono": db.query(LiderSeguro).filter(
                LiderSeguro.activo == True,
                LiderSeguro.telefono == None,
            ).count(),
        },
        "contactos_facebook": {
            "total": db.query(Contact).count(),
            "muy_activo": db.query(Contact).filter_by(segment="muy_activo").count(),
            "interesado": db.query(Contact).filter_by(segment="interesado").count(),
            "curioso": db.query(Contact).filter_by(segment="curioso").count(),
            "inactivo": db.query(Contact).filter_by(segment="inactivo").count(),
        },
        "nurturing": {
            status: count
            for status, count in db.query(
                NurturingLog.status, func.count(NurturingLog.id)
            ).group_by(NurturingLog.status).all()
        },
        "emails": {
            "pendientes": db.query(EmailQueue).filter_by(status="PENDING").count(),
            "enviados": db.query(EmailQueue).filter_by(status="SENT").count(),
        },
        "barrios": db.query(Barrio).count(),
    }