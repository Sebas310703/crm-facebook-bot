"""
lider_model.py
Modelos ORM para las tablas 'barrios' y 'lideres_seguros' de PostgreSQL.
Coincide exactamente con el schema creado en lideres_seguros.sql
"""
from datetime import datetime

from sqlalchemy import (
    Column,
    Integer,
    String,
    Boolean,
    DateTime,
    ForeignKey,
)
from sqlalchemy.orm import relationship

from database import Base


class Barrio(Base):
    __tablename__ = "barrios"

    id         = Column(Integer, primary_key=True, index=True)
    nombre     = Column(String(100), nullable=False, unique=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relación inversa → todos los líderes de este barrio
    lideres = relationship(
        "LiderSeguro",
        back_populates="barrio",
        cascade="all, delete-orphan",
    )

    def __repr__(self):
        return f"<Barrio id={self.id} nombre={self.nombre}>"


class LiderSeguro(Base):
    __tablename__ = "lideres_seguros"

    id         = Column(Integer, primary_key=True, index=True)
    nombre     = Column(String(150), nullable=False, index=True)
    cedula     = Column(String(30),  nullable=True,  index=True) 
    telefono   = Column(String(60),  nullable=True,  index=True)
    direccion  = Column(String(300), nullable=True)
    barrio_id  = Column(Integer, ForeignKey("barrios.id"), nullable=False, index=True)

    activo     = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relación con Barrio
    barrio = relationship("Barrio", back_populates="lideres")

    # ── Helpers ───────────────────────────────────────────

    def telefono_e164(self, codigo_pais: str = "57") -> str:
        """
        Convierte el teléfono al formato E.164 requerido por WhatsApp y Meta.
        Maneja teléfonos con espacios, guiones o múltiples números.

        Ejemplos:
          '3222615734'            → '+573222615734'
          '3506867946 - 3143805345' → '+573506867946'  (toma el primero)
          '+573222615734'         → '+573222615734'    (ya está en E.164)
        """
        if not self.telefono:
            return ""

        # Si hay múltiples números separados por ' - ' o '/', tomar el primero
        raw = self.telefono.split("-")[0].split("/")[0].strip()

        # Limpiar espacios y caracteres no numéricos excepto el '+'
        numero = "".join(c for c in raw if c.isdigit() or c == "+")

        if numero.startswith("+"):
            return numero          # Ya está en E.164
        if numero.startswith("0"):
            numero = numero[1:]    # Quitar el 0 inicial internacional
        if not numero:
            return ""

        return f"+{codigo_pais}{numero}"

    @property
    def nombre_barrio(self) -> str:
        """Devuelve el nombre del barrio o 'Sin barrio' si no está cargado."""
        return self.barrio.nombre if self.barrio else "Sin barrio"

    def to_dict(self) -> dict:
        """Serialización rápida para endpoints."""
        return {
            "id":          self.id,
            "nombre":      self.nombre,
            "telefono":    self.telefono,
            "telefono_e164": self.telefono_e164(),
            "direccion":   self.direccion,
            "barrio_id":   self.barrio_id,
            "barrio":      self.nombre_barrio,
            "activo":      self.activo,
            "created_at":  self.created_at.isoformat() if self.created_at else None,
            "updated_at":  self.updated_at.isoformat() if self.updated_at else None,
        }

    def __repr__(self):
        return f"<LiderSeguro id={self.id} nombre={self.nombre} barrio={self.barrio_id}>"