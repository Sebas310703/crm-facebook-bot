"""
nurturing_models.py — PolitiCRM
Modelos ORM para el sistema de nurturing automático.

Tablas:
  - nurturing_sequences → define qué mensaje se envía en qué día y canal
  - nurturing_logs      → registra cada mensaje enviado/pendiente por contacto

Estas tablas son independientes de models.py para mantener
la separación de responsabilidades entre el CRM de Facebook
y el motor de nurturing de líderes.
"""
from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from database import Base


# ================================================================
# NURTURING SEQUENCE
# ================================================================

class NurturingSequence(Base):
    """
    Define qué mensaje se envía, en qué día, para qué barrio y por qué canal.

    Lógica de prioridad:
      - sector = 'GRAN COLOMBIA' → aplica solo a ese barrio
      - sector = None            → aplica a TODOS los barrios (global)
      - Si un barrio tiene secuencia específica en día X,
        esta reemplaza la global para ese mismo (dia, orden).

    Se carga una vez con nurturing_seed.py y se puede editar
    directamente desde pgAdmin sin tocar código.
    """
    __tablename__ = "nurturing_sequences"

    id = Column(Integer, primary_key=True, index=True)

    # Barrio al que aplica. NULL = aplica a TODOS (mensaje global)
    sector = Column(String(100), nullable=True, index=True)

    # Canal de envío: "whatsapp" | "sms" | "email"
    canal  = Column(String(20), default="whatsapp", nullable=False)

    # Día desde el registro en que se envía
    # 0 = inmediato, 1 = día siguiente, 3, 7, 15, 30...
    dia    = Column(Integer, nullable=False, index=True)

    # Orden dentro del mismo día (si hay varios mensajes en el mismo día)
    orden  = Column(Integer, default=1, nullable=False)

    # Nombre de plantilla aprobada por Meta (para envíos fuera de ventana 24h)
    # Si es None, se usa el campo `mensaje` como texto libre
    template_name = Column(String(100), nullable=True)

    # Texto del mensaje. Soporta variables:
    #   {nombre}    → nombre del líder/contacto
    #   {barrio}    → barrio/sector
    #   {candidato} → nombre del candidato (desde .env)
    mensaje = Column(Text, nullable=False)

    # Control de activación — útil para pausar mensajes sin borrarlos
    activo = Column(Boolean, default=True, nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relación con logs
    logs = relationship(
        "NurturingLog",
        back_populates="sequence",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        # Garantiza unicidad: un solo mensaje por barrio + día + orden
        UniqueConstraint(
            "sector", "dia", "orden",
            name="uq_nurturing_sequence_sector_dia_orden",
        ),
        Index("ix_nurturing_seq_sector_activo", "sector", "activo"),
        Index("ix_nurturing_seq_dia_activo",    "dia",    "activo"),
    )

    def __repr__(self):
        sector_label = self.sector or "GLOBAL"
        return (
            f"<NurturingSequence id={self.id} "
            f"sector={sector_label} dia={self.dia} "
            f"orden={self.orden} canal={self.canal}>"
        )


# ================================================================
# NURTURING LOG
# ================================================================

class NurturingLog(Base):
    """
    Registra cada mensaje programado o enviado a cada contacto.

    - Evita duplicados (un contacto no recibe el mismo mensaje dos veces)
    - Permite auditar el estado completo de la secuencia
    - Soporta dos tipos de contacto: líderes y contactos de Facebook

    Estados posibles:
      PENDING  → programado, aún no enviado
      SENT     → enviado exitosamente
      FAILED   → falló el envío (ver error_msg)
      SKIPPED  → omitido (ej: secuencia eliminada, sin teléfono)
    """
    __tablename__ = "nurturing_logs"

    id = Column(Integer, primary_key=True, index=True)

    # Tipo de contacto:
    #   "lider"   → fila en tabla lideres_seguros
    #   "contact" → fila en tabla contacts (Facebook/Messenger)
    contact_type   = Column(String(20),  nullable=False, default="lider", index=True)
    contact_id     = Column(Integer,     nullable=False, index=True)

    # Datos desnormalizados para no perder info si el contacto se elimina
    contact_phone  = Column(String(60),  nullable=True)
    contact_name   = Column(String(200), nullable=True)
    contact_sector = Column(String(100), nullable=True)

    # Referencia a la secuencia que generó este log
    sequence_id = Column(
        Integer,
        ForeignKey("nurturing_sequences.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Canal usado para este mensaje específico
    canal = Column(String(20), default="whatsapp", nullable=False)

    # Estado del mensaje
    status    = Column(String(20), default="PENDING", nullable=False, index=True)
    error_msg = Column(Text, nullable=True)

    # Control temporal
    scheduled_for = Column(DateTime, nullable=False, index=True)  # Cuándo debía enviarse
    sent_at       = Column(DateTime, nullable=True)               # Cuándo se envió realmente
    created_at    = Column(DateTime, default=datetime.utcnow)

    # Relación con secuencia
    sequence = relationship("NurturingSequence", back_populates="logs")

    __table_args__ = (
        # Evitar que el mismo contacto reciba el mismo mensaje dos veces
        UniqueConstraint(
            "contact_type", "contact_id", "sequence_id",
            name="uq_nurturing_log_contact_sequence",
        ),
        # Índices compuestos para las queries más frecuentes
        Index("ix_nurturing_log_status_scheduled", "status", "scheduled_for"),
        Index("ix_nurturing_log_contact",          "contact_type", "contact_id"),
    )

    @property
    def esta_pendiente(self) -> bool:
        return self.status == "PENDING"

    @property
    def fue_enviado(self) -> bool:
        return self.status == "SENT"

    @property
    def tiempo_hasta_envio(self) -> str:
        """Retorna una descripción legible del tiempo restante hasta el envío."""
        if not self.scheduled_for:
            return "Sin programar"
        if self.status != "PENDING":
            return f"Estado: {self.status}"
        delta = self.scheduled_for - datetime.utcnow()
        if delta.total_seconds() < 0:
            return "Pendiente de procesar"
        dias  = delta.days
        horas = delta.seconds // 3600
        if dias > 0:
            return f"En {dias}d {horas}h"
        if horas > 0:
            return f"En {horas}h"
        minutos = delta.seconds // 60
        return f"En {minutos} min"

    def to_dict(self) -> dict:
        """Serialización para endpoints de administración."""
        return {
            "id":             self.id,
            "contact_type":   self.contact_type,
            "contact_id":     self.contact_id,
            "contact_name":   self.contact_name,
            "contact_phone":  self.contact_phone,
            "contact_sector": self.contact_sector,
            "sequence_id":    self.sequence_id,
            "canal":          self.canal,
            "status":         self.status,
            "error_msg":      self.error_msg,
            "scheduled_for":  self.scheduled_for.isoformat() if self.scheduled_for else None,
            "sent_at":        self.sent_at.isoformat() if self.sent_at else None,
            "tiempo_restante": self.tiempo_hasta_envio,
        }

    def __repr__(self):
        return (
            f"<NurturingLog id={self.id} "
            f"{self.contact_type}:{self.contact_id} "
            f"status={self.status} "
            f"scheduled={self.scheduled_for}>"
        )