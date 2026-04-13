"""
Modelo ORM para la tabla 'lideres' ya existente en la BD.
No modifica la tabla, solo la mapea para lectura.
"""
from sqlalchemy import Column, Integer, String
from database import Base


class Lider(Base):
    __tablename__ = "lideres"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(200))
    telefono = Column(String(20))
    direccion = Column(String(250), nullable=True)
    sector = Column(String(100), nullable=True)

    def telefono_e164(self, codigo_pais: str = "57") -> str:
        """
        Convierte el teléfono al formato E.164 requerido por WhatsApp y Twilio.
        Ejemplo: '3222615734' → '+573222615734'
        """
        numero = self.telefono.strip().replace(" ", "").replace("-", "")
        if numero.startswith("+"):
            return numero
        if numero.startswith("0"):
            numero = numero[1:]
        return f"+{codigo_pais}{numero}"

    def __repr__(self):
        return f"<Lider id={self.id} nombre={self.nombre} tel={self.telefono}>"