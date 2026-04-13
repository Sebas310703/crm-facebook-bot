from datetime import datetime
import os
import re

from fastapi import FastAPI, Depends, Request, HTTPException, Body, BackgroundTasks
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from email_sender import send_pending_emails
from facebook_api import send_facebook_message, send_facebook_private_reply
from database import SessionLocal, engine
from models import (
    Base,
    Contact,
    Event,
    EmailTemplate,
    EmailQueue,
    ConversationState,
)
from automation import run_automation

# ── NURTURING ──────────────────────────────────────────────
from nurturing_models import Base as NurturingBase
from nurturing_engine import start_scheduler, enqueue_contact, process_pending
from nurturing_models import NurturingLog, NurturingSequence
# ───────────────────────────────────────────────────────────

# =========================================================
# CONFIG / CONSTANTES
# =========================================================

FACEBOOK_VERIFY_TOKEN = os.getenv("FACEBOOK_VERIFY_TOKEN", "mi_token_de_prueba")

ENGAGEMENT_SCORE_MAP = {
    "FB_LIKE": 1,
    "FB_COMMENT": 3,
    "FB_SHARE": 5,
    "FB_MESSAGE": 4,
    "FORM_COMPLETED": 6,
}

COMMENT_KEYWORDS = {
    "INFO": {
        "reply": "👋 ¡Gracias por comentar INFO!\n\nTe escribo por aquí para ayudarte rápido.\n¿Te interesa información general o hablar con un asesor?",
        "topic": "info",
    },
    "PRECIO": {
        "reply": "💰 ¡Listo! Sobre precios: manejamos opciones según lo que necesites.\n\nPara darte un rango, ¿qué estás buscando exactamente?",
        "topic": "precio",
    },
    "ASESOR": {
        "reply": "🙋‍♂️ Perfecto. Te conecto con un asesor.\n\n¿Me confirmas tu nombre y tu WhatsApp (empieza por 3)?",
        "topic": "asesor",
    },
}

# =========================================================
# Pydantic Schemas
# =========================================================


class ContactInfo(BaseModel):
    user_id: str
    full_name: str | None = None
    email: str | None = None
    phone: str | None = None


class MessengerInput(BaseModel):
    user_id: str
    text: str


# =========================================================
# Base de datos + App
# =========================================================

Base.metadata.create_all(bind=engine)
NurturingBase.metadata.create_all(bind=engine)   # crea nurturing_sequences y nurturing_logs

app = FastAPI(title="CRM Facebook")


# ── Arrancar el scheduler al iniciar la app ───────────────
@app.on_event("startup")
def on_startup():
    start_scheduler()
# ─────────────────────────────────────────────────────────


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# =========================================================
# Helpers de negocio (sin cambios)
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
    pattern = r"^[\w\.-]+@[\w\.-]+\.\w+$"
    return re.match(pattern, email) is not None


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

        current_score = contact.engagement_score or 0
        contact.engagement_score = current_score + ENGAGEMENT_SCORE_MAP.get(event_type, 0)
        contact.last_interaction = datetime.utcnow()
        update_segment_by_score(contact)

    return event


# =========================================================
# Helpers comentarios (sin cambios)
# =========================================================


def _comment_topic(comment_id: str) -> str:
    return f"comment_id:{comment_id}"


def already_processed_comment(db: Session, comment_id: str) -> bool:
    marker = _comment_topic(comment_id)
    exists = (
        db.query(Event)
        .filter(Event.topic == marker)
        .filter(Event.event_type.in_(["FB_COMMENT", "FB_PRIVATE_REPLY_SENT"]))
        .first()
    )
    return exists is not None


def detect_keyword(comment_text: str) -> str | None:
    if not comment_text:
        return None
    t = comment_text.strip().upper()
    for kw in COMMENT_KEYWORDS.keys():
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
            "Te escribo por aquí para ayudarte rápido.\n\n"
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
# Rutas básicas
# =========================================================


@app.get("/")
def read_root():
    return {"message": "CRM Facebook funcionando 😎"}


# =========================================================
# WEBHOOK FACEBOOK
# =========================================================


@app.get("/webhook/facebook")
async def verify_facebook_webhook(request: Request):
    mode = request.query_params.get("hub.mode")
    token = request.query_params.get("hub.verify_token")
    challenge = request.query_params.get("hub.challenge")

    if mode == "subscribe" and token == FACEBOOK_VERIFY_TOKEN:
        return PlainTextResponse(challenge)
    else:
        raise HTTPException(status_code=403, detail="Verification failed")


@app.post("/webhook/facebook")
async def facebook_webhook(
    request: Request,
    background_tasks: BackgroundTasks,           # ← agregado para nurturing
    body: dict = Body(...),
    db: Session = Depends(get_db),
):
    print("[FB] Webhook body:", body)

    entries = body.get("entry", [])
    for entry in entries:

        # ─── MENSAJES MESSENGER ───────────────────────────────
        messaging_events = entry.get("messaging", [])
        for event in messaging_events:
            sender = event.get("sender", {})
            psid = sender.get("id")

            message = event.get("message")
            if not message:
                continue

            text = message.get("text")
            if not text:
                continue

            user_text = text.strip()
            contact = get_or_create_contact(db, external_id=psid)

            register_event(
                db=db,
                contact=contact,
                event_type="FB_MESSAGE",
                topic=contact.main_topic or "general",
                text=user_text,
            )

            state = get_or_create_conversation_state(db, contact)
            reply = ""

            if state.step == "start":
                reply = (
                    "👋 Hola, soy el asistente de la campaña.\n"
                    "¿Te gustaría recibir más información por correo y WhatsApp?\n"
                    "Por favor, responde con tu correo electrónico."
                )
                state.step = "ask_email"

            elif state.step == "ask_email":
                if not is_valid_email(user_text):
                    reply = (
                        "❌ El correo que escribiste no es válido.\n"
                        "Por favor escribe un correo en formato correcto "
                        "(ej: nombre@gmail.com)."
                    )
                else:
                    contact.email = user_text
                    state.step = "ask_phone"
                    reply = (
                        "✅ Correo guardado correctamente.\n"
                        "Ahora escribe tu número de WhatsApp (debe empezar por 3)."
                    )

            elif state.step == "ask_phone":
                if not is_valid_colombian_phone(user_text):
                    reply = (
                        "❌ Ese número no es válido.\n"
                        "Debe:\n"
                        "• Tener 10 dígitos\n"
                        "• Empezar por 3\n"
                        "• Solo números\n\n"
                        "Ejemplo válido: 3001234567"
                    )
                else:
                    contact.phone = user_text
                    state.step = "completed"
                    reply = (
                        "✅ ¡Perfecto! Tus datos han sido registrados correctamente.\n"
                        "Muy pronto te enviaremos información personalizada."
                    )

                    register_event(
                        db=db,
                        contact=contact,
                        event_type="FORM_COMPLETED",
                        topic=contact.main_topic or "general",
                        text="Formulario de contacto completado vía Messenger (webhook)",
                    )

                    # ── NURTURING: encolar al nuevo contacto ──────────────
                    # Se ejecuta en background para no bloquear la respuesta
                    # al usuario. El teléfono ya validado se convierte a E.164.
                    telefono_e164 = f"+57{user_text}"
                    background_tasks.add_task(
                        enqueue_contact,
                        db=SessionLocal(),          # sesión independiente para background
                        contact_id=contact.id,
                        contact_type="contact",
                        nombre=contact.full_name or "Líder",
                        telefono=telefono_e164,
                        sector=contact.main_topic,  # puedes cambiar por otro campo si tienes barrio
                    )
                    # ─────────────────────────────────────────────────────

            elif state.step == "completed":
                reply = (
                    "Ya tengo tus datos registrados 🙌.\n"
                    "Si tienes alguna pregunta específica, puedes escribirla y la analizaremos."
                )

            state.last_message = user_text
            state.updated_at = datetime.utcnow()
            db.commit()

            if reply:
                send_facebook_message(psid, reply)

        # ─── COMENTARIOS DE POSTS ─────────────────────────────
        changes = entry.get("changes", [])
        for change in changes:
            if change.get("field") != "feed":
                continue

            value = change.get("value", {}) or {}
            item = value.get("item")
            verb = value.get("verb")

            if item != "comment" or verb != "add":
                continue

            comment_id = value.get("comment_id")
            post_id = value.get("post_id")
            comment_text = value.get("message") or ""
            from_obj = value.get("from") or {}
            from_id = from_obj.get("id")
            from_name = from_obj.get("name")

            process_facebook_comment(
                db=db,
                comment_id=comment_id,
                from_id=from_id,
                from_name=from_name,
                post_id=post_id,
                comment_text=comment_text,
            )

    return {"status": "ok"}


# =========================================================
# PLANTILLAS DE EMAIL (sin cambios)
# =========================================================


@app.post("/init-templates")
def init_templates(db: Session = Depends(get_db)):
    templates_data = [
        {
            "name": "bienvenida",
            "subject": "¡Bienvenido!",
            "body": "Gracias por interactuar por primera vez con nuestro proyecto ficticio.",
        },
        {
            "name": "reenganche",
            "subject": "Te extrañamos por aquí",
            "body": "Hace varios días que no interactúas. Tenemos nuevo contenido que podría interesarte.",
        },
        {
            "name": "profundizacion_educacion",
            "subject": "Más información sobre educación",
            "body": "Vimos que te interesa el tema de educación. Aquí tienes más detalles y recursos.",
        },
    ]

    creadas = 0
    for t in templates_data:
        existe = db.query(EmailTemplate).filter_by(name=t["name"]).first()
        if not existe:
            nueva = EmailTemplate(
                name=t["name"],
                subject=t["subject"],
                body=t["body"],
                topic=None,
            )
            db.add(nueva)
            creadas += 1

    db.commit()
    return {"status": "ok", "templates_creadas": creadas}


# =========================================================
# CONTACTOS / EVENTOS (sin cambios)
# =========================================================


@app.post("/contact/update-info")
def update_contact_info(data: ContactInfo, db: Session = Depends(get_db)):
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


@app.post("/facebook/event")
def receive_event(data: dict, db: Session = Depends(get_db)):
    fb_id = data["user_id"]
    ev_type = data["type"]
    topic = data.get("topic")
    text = data.get("text")

    contact = get_or_create_contact(
        db,
        external_id=fb_id,
        default_name="Usuario Facebook",
    )

    register_event(
        db=db,
        contact=contact,
        event_type=ev_type,
        topic=topic,
        text=text,
        update_engagement=True,
    )

    db.commit()

    return {
        "status": "evento registrado",
        "contact_id": contact.id,
        "segmento": contact.segment,
        "score": contact.engagement_score,
    }


@app.post("/messenger/simulate")
def messenger_simulate(
    data: MessengerInput,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    contact = get_or_create_contact(db, external_id=data.user_id)

    user_text = data.text.strip()
    register_event(
        db=db,
        contact=contact,
        event_type="FB_MESSAGE",
        topic=contact.main_topic or "general",
        text=user_text,
    )

    state = get_or_create_conversation_state(db, contact)
    reply = ""

    if state.step == "start":
        reply = (
            "👋 Hola, soy el asistente de la campaña.\n"
            "¿Te gustaría recibir más información por correo y WhatsApp?\n"
            "Por favor, responde con tu correo electrónico."
        )
        state.step = "ask_email"

    elif state.step == "ask_email":
        if not is_valid_email(user_text):
            reply = (
                "❌ El correo que escribiste no es válido.\n"
                "Por favor escribe un correo en formato correcto "
                "(ej: nombre@gmail.com)."
            )
        else:
            contact.email = user_text
            state.step = "ask_phone"
            reply = (
                "✅ Correo guardado correctamente.\n"
                "Ahora escribe tu número de WhatsApp (debe empezar por 3)."
            )

    elif state.step == "ask_phone":
        if not is_valid_colombian_phone(user_text):
            reply = (
                "❌ Ese número no es válido.\n"
                "Debe:\n"
                "• Tener 10 dígitos\n"
                "• Empezar por 3\n"
                "• Solo números\n\n"
                "Ejemplo válido: 3001234567"
            )
        else:
            contact.phone = user_text
            state.step = "completed"
            reply = (
                "¡Gracias! ✅ He registrado tu correo y tu número.\n"
                "En breve te enviaremos información personalizada sobre el proyecto."
            )

            register_event(
                db=db,
                contact=contact,
                event_type="FORM_COMPLETED",
                topic=contact.main_topic or "general",
                text="Formulario de contacto completado vía Messenger (simulado)",
            )

            # ── NURTURING: encolar al nuevo contacto ──────────────
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
            # ─────────────────────────────────────────────────────

    elif state.step == "completed":
        reply = (
            "Ya tengo tus datos registrados 🙌.\n"
            "Si tienes alguna pregunta específica, puedes escribirla y la analizaremos."
        )

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
# AUTOMATIZACIÓN Y EMAILS (sin cambios)
# =========================================================


@app.post("/automation/run")
def run_automation_endpoint(db: Session = Depends(get_db)):
    run_automation(db)
    pendientes = db.query(EmailQueue).filter_by(status="PENDING").count()
    return {"status": "automation_ejecutada", "emails_pendientes": pendientes}


@app.get("/emails/pending")
def get_pending_emails(db: Session = Depends(get_db)):
    emails = db.query(EmailQueue).filter_by(status="PENDING").all()
    resultado = []
    for e in emails:
        resultado.append(
            {
                "id": e.id,
                "contact_id": e.contact_id,
                "template_id": e.template_id,
                "scheduled_at": e.scheduled_at,
            }
        )
    return resultado


# =========================================================
# NURTURING — endpoints de administración
# =========================================================


@app.get("/nurturing/stats")
def nurturing_stats(db: Session = Depends(get_db)):
    """Estado actual de todos los mensajes programados."""
    from sqlalchemy import func
    stats = (
        db.query(NurturingLog.status, func.count(NurturingLog.id))
        .group_by(NurturingLog.status)
        .all()
    )
    return {status: count for status, count in stats}


@app.post("/nurturing/encolar-lideres")
def encolar_lideres_existentes():
    """
    Encola la secuencia completa para los 800 líderes ya existentes.
    Ejecutar UNA sola vez desde Swagger en /docs.
    """
    from nurturing_engine import enqueue_lideres_existentes
    total = enqueue_lideres_existentes()
    return {"mensajes_programados": total}


@app.post("/nurturing/procesar-ahora")
def procesar_ahora():
    """Fuerza el envío inmediato de mensajes pendientes. Útil para pruebas."""
    return process_pending(batch_size=5)