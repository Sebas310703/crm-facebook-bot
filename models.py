from datetime import datetime

from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    DateTime,
    ForeignKey,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from database import Base


class Contact(Base):
    __tablename__ = "contacts"

    id = Column(Integer, primary_key=True, index=True)
    # ID externo del canal (por ahora, PSID de Facebook/Messenger)
    external_id = Column(String, unique=True, index=True)

    full_name = Column(String, default="Usuario Facebook")
    email = Column(String, nullable=True)
    phone = Column(String, nullable=True)  # WhatsApp u otro

    # Segmento de marketing según engagement
    segment = Column(String, default="nuevo")

    # Estado en el embudo comercial (podemos usarlo luego en automatización)
    # Ej: nuevo_lead, lead_calificado, cliente, churn_risk, etc.
    lifecycle_stage = Column(String, default="nuevo_lead")

    # Puntuación de interacción (likes, mensajes, formularios, etc.)
    engagement_score = Column(Float, default=0)

    # Tema principal de interés detectado (educacion, empleo, etc.)
    main_topic = Column(String, nullable=True)

    # De qué canal/proyecto vino el lead (facebook_messenger, formulario_web, etc.)
    source = Column(String, default="facebook_messenger")

    # Trazabilidad temporal
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Última vez que interactuó (cualquier canal)
    last_interaction = Column(DateTime, default=datetime.utcnow)

    # --------- Relaciones ORM (muy útiles para dashboard/IA) ---------
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


class Event(Base):
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, index=True)
    contact_id = Column(Integer, ForeignKey("contacts.id"), index=True)

    # Tipo de evento: FB_LIKE, FB_COMMENT, FB_SHARE, FB_MESSAGE, FORM_COMPLETED, etc.
    event_type = Column(String, index=True)

    # Canal donde ocurrió: messenger, email, whatsapp, interno, etc.
    channel = Column(String, default="messenger")

    # Tema asociado al evento: educacion, empleo, etc.
    topic = Column(String, nullable=True)

    # Texto asociado (ej: mensaje del usuario, comentario, etc.)
    text = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    # Relación inversa
    contact = relationship("Contact", back_populates="events")


class EmailTemplate(Base):
    __tablename__ = "email_templates"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)  # "bienvenida", "reenganche"
    subject = Column(String)
    body = Column(Text)
    topic = Column(String, nullable=True)  # opcional: educación, empleo, etc.


class EmailQueue(Base):
    __tablename__ = "email_queue"

    id = Column(Integer, primary_key=True, index=True)
    contact_id = Column(Integer, ForeignKey("contacts.id"), index=True)
    template_id = Column(Integer, ForeignKey("email_templates.id"), index=True)

    scheduled_at = Column(DateTime, default=datetime.utcnow)
    status = Column(String, default="PENDING")  # PENDING, SENT

    # Para trazabilidad futura
    sent_at = Column(DateTime, nullable=True)

    # Relaciones
    contact = relationship("Contact", back_populates="emails")
    template = relationship("EmailTemplate")

    __table_args__ = (
        # Evitar duplicados exactos de misma campaña al mismo contacto en el mismo segundo (opcional)
        UniqueConstraint("contact_id", "template_id", "scheduled_at", name="uq_emailqueue_contact_template_time"),
    )


class ConversationState(Base):
    __tablename__ = "conversation_state"

    id = Column(Integer, primary_key=True, index=True)
    contact_id = Column(Integer, ForeignKey("contacts.id"), index=True)

    # Canal de conversación: messenger / whatsapp / webchat, etc.
    channel = Column(String, default="messenger")

    # Estado de la “máquina de estados” del bot: start, ask_email, ask_phone, completed
    step = Column(String, default="start")

    last_message = Column(Text, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow)

    # Relación inversa
    contact = relationship("Contact", back_populates="conversation_states")

    __table_args__ = (
        # Garantizamos un solo estado por contacto+canal
        UniqueConstraint("contact_id", "channel", name="uq_conversation_state_contact_channel"),
    )
