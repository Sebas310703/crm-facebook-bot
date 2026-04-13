from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text
from datetime import datetime
from database import Base


class Contact(Base):
    __tablename__ = "contacts"

    id = Column(Integer, primary_key=True, index=True)
    external_id = Column(String, unique=True, index=True)  # ID de Facebook/Messenger
    full_name = Column(String, default="Usuario Facebook")
    email = Column(String, nullable=True)
    phone = Column(String, nullable=True)   # ← NUEVO

    segment = Column(String, default="nuevo")
    engagement_score = Column(Float, default=0)
    main_topic = Column(String, nullable=True)

    last_interaction = Column(DateTime, default=datetime.utcnow)



class Event(Base):
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, index=True)
    contact_id = Column(Integer, ForeignKey("contacts.id"))

    event_type = Column(String)     # FB_LIKE, FB_COMMENT, FB_SHARE, FB_MESSAGE
    topic = Column(String)          # educacion, empleo, etc.
    text = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)


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
    contact_id = Column(Integer, ForeignKey("contacts.id"))
    template_id = Column(Integer, ForeignKey("email_templates.id"))
    scheduled_at = Column(DateTime, default=datetime.utcnow)
    status = Column(String, default="PENDING")  # PENDING, SENT

class ConversationState(Base):
    __tablename__ = "conversation_state"

    id = Column(Integer, primary_key=True, index=True)
    contact_id = Column(Integer, ForeignKey("contacts.id"))
    channel = Column(String, default="messenger")  # messenger / whatsapp, etc.
    step = Column(String, default="start")         # start, ask_email, ask_phone, completed
    last_message = Column(Text, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow)
