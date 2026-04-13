from fastapi import FastAPI, Depends, Request, HTTPException, Body
from sqlalchemy.orm import Session
from datetime import datetime
from email_sender import send_pending_emails
from pydantic import BaseModel
import os
from fastapi.responses import PlainTextResponse

from facebook_api import send_facebook_message

from database import SessionLocal, engine
from models import Base, Contact, Event, EmailTemplate, EmailQueue, ConversationState
from automation import run_automation

# Token de verificación que usarás también en Meta Developers
FACEBOOK_VERIFY_TOKEN = os.getenv("FACEBOOK_VERIFY_TOKEN", "mi_token_de_prueba")


# ===================== Pydantic Schemas =====================

class ContactInfo(BaseModel):
    user_id: str                # mismo ID que uses en user_id (ej: "fb_001" o psid)
    full_name: str | None = None
    email: str | None = None
    phone: str | None = None


class MessengerInput(BaseModel):
    user_id: str
    text: str


# ===================== Base de datos =====================

# Crear las tablas automáticamente
Base.metadata.create_all(bind=engine)

app = FastAPI(title="CRM Facebook")


# Dependencia para usar la DB
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_or_create_conversation_state(db: Session, contact: Contact) -> ConversationState:
    state = db.query(ConversationState).filter_by(
        contact_id=contact.id,
        channel="messenger"
    ).first()

    if not state:
        state = ConversationState(
            contact_id=contact.id,
            channel="messenger",
            step="start"
        )
        db.add(state)
        db.commit()
        db.refresh(state)

    return state


# ===================== Rutas básicas =====================

@app.get("/")
def read_root():
    return {"message": "CRM Facebook funcionando 😎"}


# ===================== WEBHOOK FACEBOOK =====================

@app.get("/webhook/facebook")
async def verify_facebook_webhook(request: Request):
    """
    Endpoint que usa Facebook para verificar el webhook (solo GET).
    """
    mode = request.query_params.get("hub.mode")
    token = request.query_params.get("hub.verify_token")
    challenge = request.query_params.get("hub.challenge")

    if mode == "subscribe" and token == FACEBOOK_VERIFY_TOKEN:
        # Devuelve el challenge tal cual en texto plano
        return PlainTextResponse(challenge)
    else:
        raise HTTPException(status_code=403, detail="Verification failed")


@app.post("/webhook/facebook")
async def facebook_webhook(
    body: dict = Body(...),
    db: Session = Depends(get_db)
):
    """
    Recibe eventos reales desde Facebook (Messenger).
    Para cada mensaje de texto, aplica la lógica del bot
    y responde por Messenger usando Graph API.
    """
    print("[FB] Webhook body:", body)

    entries = body.get("entry", [])
    for entry in entries:
        messaging_events = entry.get("messaging", [])
        for event in messaging_events:
            sender = event.get("sender", {})
            psid = sender.get("id")

            # Solo manejamos mensajes de texto sencillos
            message = event.get("message")
            if not message:
                continue

            text = message.get("text")
            if not text:
                continue

            # ======= LÓGICA DEL BOT (igual que /messenger/simulate) =======
            # 1. Buscar o crear contacto
            contact = db.query(Contact).filter_by(external_id=psid).first()
            if not contact:
                contact = Contact(external_id=psid)
                db.add(contact)
                db.commit()
                db.refresh(contact)

            # 2. Obtener o crear estado de conversación
            state = get_or_create_conversation_state(db, contact)

            user_text = text.strip()
            reply = ""

            if state.step == "start":
                reply = (
                    "👋 Hola, soy el asistente de la campaña.\n"
                    "¿Te gustaría recibir más información por correo y WhatsApp?\n"
                    "Por favor, responde con tu correo electrónico."
                )
                state.step = "ask_email"

            elif state.step == "ask_email":
                contact.email = user_text
                state.step = "ask_phone"
                reply = (
                    "Perfecto, he guardado tu correo 📧.\n"
                    "Ahora, por favor escribe tu número de WhatsApp (solo números)."
                )

            elif state.step == "ask_phone":
                contact.phone = user_text
                state.step = "completed"
                reply = (
                    "¡Gracias! ✅ He registrado tu correo y tu número.\n"
                    "En breve te enviaremos información personalizada sobre el proyecto."
                )

                event_obj = Event(
                    contact_id=contact.id,
                    event_type="FORM_COMPLETED",
                    topic=contact.main_topic or "general",
                    text="Formulario de contacto completado vía Messenger (webhook)"
                )
                db.add(event_obj)

            elif state.step == "completed":
                reply = (
                    "Ya tengo tus datos registrados 🙌.\n"
                    "Si tienes alguna pregunta específica, puedes escribirla y la analizaremos."
                )

            # 3. Actualizar estado
            state.last_message = user_text
            state.updated_at = datetime.utcnow()

            db.commit()

            # 4. Enviar respuesta a Messenger (si hay token configurado)
            if reply:
                send_facebook_message(psid, reply)

    return {"status": "ok"}


# ===================== PLANTILLAS DE EMAIL =====================

@app.post("/init-templates")
def init_templates(db: Session = Depends(get_db)):
    """
    Crea algunas plantillas básicas de email si no existen.
    """
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
                topic=None
            )
            db.add(nueva)
            creadas += 1

    db.commit()
    return {"status": "ok", "templates_creadas": creadas}


# ===================== CONTACTOS / EVENTOS =====================

@app.post("/contact/update-info")
def update_contact_info(data: ContactInfo, db: Session = Depends(get_db)):
    """
    Actualiza la info de contacto (nombre, email, teléfono) para un usuario.
    Simula que la persona te dio esos datos por un formulario o por chat.
    """
    contact = db.query(Contact).filter_by(external_id=data.user_id).first()
    if not contact:
        contact = Contact(external_id=data.user_id)
        db.add(contact)

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
        "phone": contact.phone
    }


@app.post("/facebook/event")
def receive_event(data: dict, db: Session = Depends(get_db)):

    fb_id = data["user_id"]
    ev_type = data["type"]
    topic = data.get("topic")
    text = data.get("text")

    # 1. Buscar el contacto por su ID de Facebook
    contact = db.query(Contact).filter_by(external_id=fb_id).first()

    # 2. Si no existe, se crea automáticamente
    if not contact:
        contact = Contact(
            external_id=fb_id,
            full_name="Usuario Facebook"
        )
        db.add(contact)
        db.commit()
        db.refresh(contact)

    # 3. Registrar el evento
    event = Event(
        contact_id=contact.id,
        event_type=ev_type,
        topic=topic,
        text=text
    )
    db.add(event)

    # 4. Si no tiene tema principal, asignar el de este evento
    if topic and not contact.main_topic:
        contact.main_topic = topic

    # 5. Actualizar engagement
    score_map = {
        "FB_LIKE": 1,
        "FB_COMMENT": 3,
        "FB_SHARE": 5,
        "FB_MESSAGE": 4
    }

    contact.engagement_score += score_map.get(ev_type, 0)
    contact.last_interaction = datetime.utcnow()

    # 6. Segmentación automática
    if contact.engagement_score >= 40:
        contact.segment = "muy_activo"
    elif contact.engagement_score >= 15:
        contact.segment = "interesado"
    elif contact.engagement_score > 0:
        contact.segment = "curioso"
    else:
        contact.segment = "inactivo"

    db.commit()

    return {
        "status": "evento registrado",
        "contact_id": contact.id,
        "segmento": contact.segment,
        "score": contact.engagement_score
    }


@app.post("/messenger/simulate")
def messenger_simulate(data: MessengerInput, db: Session = Depends(get_db)):
    """
    Simula una conversación de Messenger con el bot.
    Va guiando al usuario para recoger email y teléfono.
    """

    # 1. Buscar o crear contacto
    contact = db.query(Contact).filter_by(external_id=data.user_id).first()
    if not contact:
        contact = Contact(external_id=data.user_id)
        db.add(contact)
        db.commit()
        db.refresh(contact)

    # 2. Obtener o crear estado de conversación
    state = get_or_create_conversation_state(db, contact)

    user_text = data.text.strip()

    # 3. Lógica de estados
    reply = ""

    if state.step == "start":
        reply = (
            "👋 Hola, soy el asistente de la campaña.\n"
            "¿Te gustaría recibir más información por correo y WhatsApp?\n"
            "Por favor, responde con tu correo electrónico."
        )
        state.step = "ask_email"

    elif state.step == "ask_email":
        contact.email = user_text
        state.step = "ask_phone"
        reply = (
            "Perfecto, he guardado tu correo 📧.\n"
            "Ahora, por favor escribe tu número de WhatsApp (solo números)."
        )

    elif state.step == "ask_phone":
        contact.phone = user_text
        state.step = "completed"
        reply = (
            "¡Gracias! ✅ He registrado tu correo y tu número.\n"
            "En breve te enviaremos información personalizada sobre el proyecto."
        )

        event = Event(
            contact_id=contact.id,
            event_type="FORM_COMPLETED",
            topic=contact.main_topic or "general",
            text="Formulario de contacto completado vía Messenger"
        )
        db.add(event)

    elif state.step == "completed":
        reply = (
            "Ya tengo tus datos registrados 🙌.\n"
            "Si tienes alguna pregunta específica, puedes escribirla y la analizaremos."
        )

    # 4. Actualizar estado
    state.last_message = user_text
    state.updated_at = datetime.utcnow()

    # 5. Guardar cambios de contacto + estado
    db.commit()

    return {
        "status": "ok",
        "bot_reply": reply,
        "conversation_step": state.step,
        "contact": {
            "id": contact.id,
            "email": contact.email,
            "phone": contact.phone
        }
    }


# ===================== AUTOMATIZACIÓN Y EMAILS =====================

@app.post("/automation/run")
def run_automation_endpoint(db: Session = Depends(get_db)):
    """
    Ejecuta el motor de automatización.
    Revisa contactos y programa emails en la cola.
    """
    run_automation(db)
    pendientes = db.query(EmailQueue).filter_by(status="PENDING").count()
    return {"status": "automation_ejecutada", "emails_pendientes": pendientes}


@app.get("/emails/pending")
def get_pending_emails(db: Session = Depends(get_db)):
    """
    Lista los emails pendientes de envío.
    """
    emails = db.query(EmailQueue).filter_by(status="PENDING").all()
    resultado = []
    for e in emails:
        resultado.append({
            "id": e.id,
            "contact_id": e.contact_id,
            "template_id": e.template_id,
            "scheduled_at": e.scheduled_at
        })
    return resultado


@app.post("/emails/send-pending")
def send_emails_endpoint(db: Session = Depends(get_db)):
    """
    Simula el envío de todos los emails en estado PENDING.
    """
    enviados = send_pending_emails(db)
    return {"status": "ok", "emails_enviados": enviados}
