"""
models.py — PolitiCRM
Modelos ORM definitivos. Combina la versión inicial (Backend/)
con la versión avanzada de la raíz.

Tablas:
  - contacts            → contactos de Facebook/Messenger
  - events              → eventos de interacción
  - email_templates     → plantillas de correo
  - email_queue         → cola de envío de emails
  - conversation_state  → estado del bot por contacto y canal
"""
from datetime import datetime

from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    Boolean,
    DateTime,
    ForeignKey,
    Text,
    UniqueConstraint,
    Index,
)
from sqlalchemy.orm import relationship

from database import Base


# =========================================================
# CONTACT
# =========================================================

class Contact(Base):
    __tablename__ = "contacts"

    id          = Column(Integer, primary_key=True, index=True)

    # ID externo del canal (PSID de Facebook/Messenger, etc.)
    external_id = Column(String(100), unique=True, index=True, nullable=False)

    full_name   = Column(String(200), default="Usuario Facebook")
    email       = Column(String(200), nullable=True)
    phone       = Column(String(60),  nullable=True)   # WhatsApp u otro canal

    # ── Segmentación ──────────────────────────────────────
    # Segmento de marketing según engagement
    # Valores: nuevo | curioso | interesado | muy_activo | inactivo
    segment     = Column(String(50), default="nuevo", index=True)

    # Etapa en el embudo comercial
    # Valores: nuevo_lead | lead_calificado | cliente | churn_risk
    lifecycle_stage = Column(String(50), default="nuevo_lead")

    # Puntuación de interacción acumulada
    engagement_score = Column(Float, default=0)

    # Tema principal de interés detectado (educacion, empleo, salud, etc.)
    main_topic  = Column(String(100), nullable=True)

    # Canal/origen del lead (facebook_messenger, formulario_web, whatsapp, etc.)
    source      = Column(String(100), default="facebook_messenger")

    # ── Trazabilidad temporal ─────────────────────────────
    created_at       = Column(DateTime, default=datetime.utcnow)
    updated_at       = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_interaction = Column(DateTime, default=datetime.utcnow)

    # ── Relaciones ORM ────────────────────────────────────
    events = relationship(
        "Event",
        back_populates="contact",
        cascade="all, delete-orphan",
    )
    emails = relationship(
        "EmailQueue",
        back_populates="contact",
        cascade="all, delete-orphan",
    )
    conversation_states = relationship(
        "ConversationState",
        back_populates="contact",
        cascade="all, delete-orphan",
    )

    def __repr__(self):
        return f"<Contact id={self.id} external_id={self.external_id} segment={self.segment}>"


# =========================================================
# EVENT
# =========================================================

class Event(Base):
    __tablename__ = "events"

    id         = Column(Integer, primary_key=True, index=True)
    contact_id = Column(Integer, ForeignKey("contacts.id"), nullable=False, index=True)

    # Tipo de evento
    # Valores: FB_LIKE | FB_COMMENT | FB_SHARE | FB_MESSAGE |
    #          FORM_COMPLETED | FB_PRIVATE_REPLY_SENT | FB_PRIVATE_REPLY_FAILED
    event_type = Column(String(50), nullable=False, index=True)

    # Canal donde ocurrió: messenger | email | whatsapp | interno
    channel    = Column(String(30), default="messenger")

    # Tema asociado al evento
    topic      = Column(String(200), nullable=True)

    # Texto asociado (mensaje del usuario, comentario, etc.)
    text       = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    # Relación inversa
    contact = relationship("Contact", back_populates="events")

    __table_args__ = (
        Index("ix_events_contact_type", "contact_id", "event_type"),
    )

    def __repr__(self):
        return f"<Event id={self.id} type={self.event_type} contact_id={self.contact_id}>"


# =========================================================
# EMAIL TEMPLATE
# =========================================================

class EmailTemplate(Base):
    __tablename__ = "email_templates"

    id      = Column(Integer, primary_key=True, index=True)
    name    = Column(String(100), unique=True, index=True, nullable=False)
    subject = Column(String(300), nullable=False)
    body    = Column(Text, nullable=False)

    # Tema asociado (educacion, empleo, salud, etc.) — opcional
    topic   = Column(String(100), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    # Relación
    queue_items = relationship(
        "EmailQueue",
        back_populates="template",
        cascade="all, delete-orphan",
    )

    def __repr__(self):
        return f"<EmailTemplate id={self.id} name={self.name}>"


# =========================================================
# EMAIL QUEUE
# =========================================================

class EmailQueue(Base):
    __tablename__ = "email_queue"

    id          = Column(Integer, primary_key=True, index=True)
    contact_id  = Column(Integer, ForeignKey("contacts.id"),       nullable=False, index=True)
    template_id = Column(Integer, ForeignKey("email_templates.id"), nullable=False, index=True)

    scheduled_at = Column(DateTime, default=datetime.utcnow)

    # Estado: PENDING | SENT | FAILED
    status   = Column(String(20), default="PENDING", index=True)
    sent_at  = Column(DateTime, nullable=True)   # Cuándo se envió realmente

    # Trazabilidad de errores
    error_msg = Column(Text, nullable=True)

    # Relaciones
    contact  = relationship("Contact",       back_populates="emails")
    template = relationship("EmailTemplate", back_populates="queue_items")

    __table_args__ = (
        # Evitar duplicados exactos: mismo contacto + misma plantilla + mismo momento
        UniqueConstraint(
            "contact_id", "template_id", "scheduled_at",
            name="uq_emailqueue_contact_template_time",
        ),
        Index("ix_emailqueue_status_scheduled", "status", "scheduled_at"),
    )

    def __repr__(self):
        return f"<EmailQueue id={self.id} contact={self.contact_id} status={self.status}>"


# =========================================================
# CONVERSATION STATE
# =========================================================

class ConversationState(Base):
    __tablename__ = "conversation_state"

    id         = Column(Integer, primary_key=True, index=True)
    contact_id = Column(Integer, ForeignKey("contacts.id"), nullable=False, index=True)

    # Canal de conversación: messenger | whatsapp | webchat
    channel    = Column(String(30), default="messenger")

    # Paso actual en la máquina de estados del bot
    # Valores: start | ask_email | ask_phone | completed
    step       = Column(String(50), default="start")

    last_message = Column(Text, nullable=True)
    updated_at   = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relación inversa
    contact = relationship("Contact", back_populates="conversation_states")

    __table_args__ = (
        # Un solo estado activo por contacto + canal
        UniqueConstraint(
            "contact_id", "channel",
            name="uq_conversation_state_contact_channel",
        ),
    )

    def __repr__(self):
        return f"<ConversationState contact={self.contact_id} channel={self.channel} step={self.step}>"