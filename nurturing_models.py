"""
nurturing_models.py
Modelos para el sistema de nurturing automático.
Agregar a models.py o importar desde aquí.
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from database import Base


class NurturingSequence(Base):
    """
    Define qué mensaje se envía en qué día para cada barrio y canal.
    Se carga una vez con seed_sequences() y se puede editar desde pgAdmin.
    """
    __tablename__ = "nurturing_sequences"

    id = Column(Integer, primary_key=True, index=True)

    # Barrio al que aplica. NULL = aplica a TODOS los barrios (mensaje global)
    sector = Column(String(100), nullable=True, index=True)

    # Canal: "whatsapp", "sms", "email"
    canal = Column(String(20), default="whatsapp")

    # Día desde el registro en que se envía (0=inmediato, 1=día siguiente, etc.)
    dia = Column(Integer, index=True)

    # Nombre de la plantilla en Meta (para WhatsApp fuera de ventana 24h)
    template_name = Column(String(100), nullable=True)

    # Texto del mensaje. Soporta variables: {nombre}, {barrio}, {candidato}
    mensaje = Column(Text, nullable=False)

    # Orden dentro del mismo día (por si hay varios mensajes en el mismo día)
    orden = Column(Integer, default=1)

    activo = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    logs = relationship("NurturingLog", back_populates="sequence")


class NurturingLog(Base):
    """
    Registra cada mensaje enviado a cada contacto.
    Evita duplicados y permite auditar el estado de la secuencia.
    """
    __tablename__ = "nurturing_logs"

    id = Column(Integer, primary_key=True, index=True)

    # Puede ser un líder (tabla lideres) o un contacto nuevo (tabla contacts)
    # Guardamos tipo + id para soportar ambas tablas
    contact_type = Column(String(20), default="lider")  # "lider" o "contact"
    contact_id = Column(Integer, index=True)
    contact_phone = Column(String(20))
    contact_name = Column(String(200))
    contact_sector = Column(String(100), nullable=True)

    sequence_id = Column(Integer, ForeignKey("nurturing_sequences.id"), index=True)

    canal = Column(String(20), default="whatsapp")
    status = Column(String(20), default="PENDING")  # PENDING, SENT, FAILED, SKIPPED
    error_msg = Column(Text, nullable=True)

    scheduled_for = Column(DateTime, index=True)   # Cuándo debía enviarse
    sent_at = Column(DateTime, nullable=True)       # Cuándo se envió realmente

    created_at = Column(DateTime, default=datetime.utcnow)

    sequence = relationship("NurturingSequence", back_populates="logs")