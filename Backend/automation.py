"""
automation.py — PolitiCRM
Motor de automatización de emails basado en reglas.

Responsabilidad:
  - Evalúa todos los contactos de Facebook/Messenger
  - Aplica reglas de negocio para programar emails automáticos
  - Evita duplicados en la cola de envío

Reglas actuales:
  1. Bienvenida        → engagement > 0
  2. Reenganche        → sin interacción hace 7+ días
  3. Por tema          → profundización según main_topic del contacto
  4. Muy activo        → score >= 40, reconocimiento especial
  5. Lead calificado   → formulario completado (FORM_COMPLETED)

Uso:
  - Desde endpoint:  POST /automation/run
  - Desde scheduler: llamar run_automation(db) cada cierto tiempo
"""
import logging
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from models import Contact, Event, EmailTemplate, EmailQueue

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s [AUTOMATION] %(message)s")

# =========================================================
# REGLAS DE NEGOCIO — configuración central
# =========================================================

# Días sin interacción para disparar reenganche
REENGANCHE_DIAS = 7

# Score mínimo para considerar un contacto "muy activo"
SCORE_MUY_ACTIVO = 40

# Score mínimo para profundización por tema
SCORE_PROFUNDIZACION = 15

# Temas con plantilla de profundización disponible
TEMAS_CON_PLANTILLA = {
    "educacion":   "profundizacion_educacion",
    "empleo":      "profundizacion_empleo",
    "salud":       "profundizacion_salud",
    "seguridad":   "profundizacion_seguridad",
    "info":        "profundizacion_info",
}


# =========================================================
# HELPER — programar email en la cola
# =========================================================

def schedule_email(
    db: Session,
    contact_id: int,
    template_name: str,
    delay_hours: int = 0,
) -> bool:
    """
    Crea un registro en la cola de emails si no existe uno PENDING
    para ese contacto y esa plantilla.

    Args:
        db:            Sesión de SQLAlchemy.
        contact_id:    ID del contacto destino.
        template_name: Nombre de la plantilla (debe existir en email_templates).
        delay_hours:   Horas de retraso desde ahora para el envío (default: 0).

    Returns:
        True si se programó, False si ya existía o la plantilla no existe.
    """
    # Verificar que la plantilla existe
    template = db.query(EmailTemplate).filter_by(name=template_name).first()
    if not template:
        logger.warning(f"Plantilla '{template_name}' no encontrada — omitiendo")
        return False

    # Evitar duplicados PENDING
    already_pending = (
        db.query(EmailQueue)
        .filter_by(
            contact_id=contact_id,
            template_id=template.id,
            status="PENDING",
        )
        .first()
    )
    if already_pending:
        return False

    scheduled_at = datetime.utcnow() + timedelta(hours=delay_hours)

    email_q = EmailQueue(
        contact_id=contact_id,
        template_id=template.id,
        scheduled_at=scheduled_at,
        status="PENDING",
    )
    db.add(email_q)
    logger.info(
        f"✓ Email '{template_name}' programado para contacto {contact_id} "
        f"en {scheduled_at.strftime('%Y-%m-%d %H:%M')} UTC"
    )
    return True


# =========================================================
# HELPERS — verificar eventos del contacto
# =========================================================

def contact_completed_form(db: Session, contact_id: int) -> bool:
    """Retorna True si el contacto completó el formulario de contacto."""
    return (
        db.query(Event)
        .filter_by(contact_id=contact_id, event_type="FORM_COMPLETED")
        .first()
    ) is not None


def days_since_last_interaction(contact: Contact) -> float:
    """Retorna los días transcurridos desde la última interacción."""
    if not contact.last_interaction:
        return 999
    delta = datetime.utcnow() - contact.last_interaction
    return delta.total_seconds() / 86400


# =========================================================
# MOTOR PRINCIPAL
# =========================================================

def run_automation(db: Session) -> dict:
    """
    Motor principal de automatización.
    Evalúa todos los contactos y aplica las reglas de email.

    Returns:
        Dict con resumen de emails programados por regla.
    """
    now = datetime.utcnow()
    contactos = db.query(Contact).all()

    resumen = {
        "total_contactos": len(contactos),
        "bienvenida":           0,
        "reenganche":           0,
        "profundizacion":       0,
        "muy_activo":           0,
        "lead_calificado":      0,
    }

    logger.info(f"Iniciando automation para {len(contactos)} contactos...")

    for c in contactos:
        score = c.engagement_score or 0
        dias_inactivo = days_since_last_interaction(c)

        # ── REGLA 1: Bienvenida ───────────────────────────
        # Contacto con cualquier interacción que aún no recibió bienvenida
        if score > 0:
            if schedule_email(db, c.id, "bienvenida"):
                resumen["bienvenida"] += 1

        # ── REGLA 2: Reenganche ───────────────────────────
        # Sin interacción hace REENGANCHE_DIAS días
        if score > 0 and dias_inactivo >= REENGANCHE_DIAS:
            if schedule_email(db, c.id, "reenganche", delay_hours=2):
                resumen["reenganche"] += 1

        # ── REGLA 3: Profundización por tema ──────────────
        # Score suficiente y tiene tema principal con plantilla disponible
        if score >= SCORE_PROFUNDIZACION and c.main_topic:
            template_name = TEMAS_CON_PLANTILLA.get(c.main_topic)
            if template_name:
                if schedule_email(db, c.id, template_name, delay_hours=1):
                    resumen["profundizacion"] += 1

        # ── REGLA 4: Muy activo ───────────────────────────
        # Score muy alto → reconocimiento especial
        if score >= SCORE_MUY_ACTIVO:
            if schedule_email(db, c.id, "reconocimiento_activo", delay_hours=0):
                resumen["muy_activo"] += 1

        # ── REGLA 5: Lead calificado ──────────────────────
        # Completó el formulario con email y teléfono
        if c.email and c.phone and contact_completed_form(db, c.id):
            if schedule_email(db, c.id, "lead_calificado", delay_hours=0):
                resumen["lead_calificado"] += 1

    db.commit()

    total_programados = sum(v for k, v in resumen.items() if k != "total_contactos")
    logger.info(f"✓ Automation completa — {total_programados} emails programados: {resumen}")

    return resumen


# =========================================================
# HELPER — limpiar cola de emails enviados
# =========================================================

def limpiar_cola_enviados(db: Session, dias: int = 30) -> int:
    """
    Elimina emails en estado SENT o FAILED con más de `dias` días de antigüedad.
    Útil para mantenimiento periódico de la tabla email_queue.

    Args:
        db:   Sesión de SQLAlchemy.
        dias: Emails más viejos que este número de días serán eliminados.

    Returns:
        Número de registros eliminados.
    """
    fecha_limite = datetime.utcnow() - timedelta(days=dias)
    eliminados = (
        db.query(EmailQueue)
        .filter(
            EmailQueue.status.in_(["SENT", "FAILED"]),
            EmailQueue.scheduled_at < fecha_limite,
        )
        .delete(synchronize_session=False)
    )
    db.commit()
    logger.info(f"✓ Cola limpiada — {eliminados} registros eliminados (>{dias} días)")
    return eliminados