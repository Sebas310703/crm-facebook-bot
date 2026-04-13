from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from models import Contact, EmailTemplate, EmailQueue


# =========================================================
# Helpers para campañas de email
# =========================================================

def _get_template(db: Session, template_name: str) -> EmailTemplate | None:
    return db.query(EmailTemplate).filter_by(name=template_name).first()


def _has_recent_email(
    db: Session,
    contact_id: int,
    template_id: int,
    window_days: int = 7,
) -> bool:
    """
    Verifica si ya se envió (o programó) un email de esta plantilla
    para el contacto en los últimos `window_days` días.
    Evita spamear al mismo lead con la misma campaña.
    """
    cutoff = datetime.utcnow() - timedelta(days=window_days)

    recent = (
        db.query(EmailQueue)
        .filter(
            EmailQueue.contact_id == contact_id,
            EmailQueue.template_id == template_id,
            EmailQueue.scheduled_at >= cutoff,
        )
        .first()
    )
    return recent is not None


def schedule_email(
    db: Session,
    contact_id: int,
    template_name: str,
    delay_minutes: int = 0,
    cooldown_days: int = 7,
) -> None:
    """
    Crea un registro en la cola de emails para una plantilla dada,
    respetando:
    - Que exista la plantilla.
    - Que no haya otro email PENDING de esa plantilla para el contacto.
    - Que no se haya enviado/programado uno igual en los últimos `cooldown_days`.
    """

    template = _get_template(db, template_name)
    if not template:
        print(f"[AUTOMATION] Plantilla '{template_name}' no existe")
        return

    # 1. Evitar duplicados pendientes
    pending = (
        db.query(EmailQueue)
        .filter_by(contact_id=contact_id, template_id=template.id, status="PENDING")
        .first()
    )
    if pending:
        return

    # 2. Evitar SPAM: no repetir misma campaña muy seguido
    if _has_recent_email(db, contact_id, template.id, window_days=cooldown_days):
        return

    scheduled_time = datetime.utcnow() + timedelta(minutes=delay_minutes)

    email_q = EmailQueue(
        contact_id=contact_id,
        template_id=template.id,
        scheduled_at=scheduled_time,
        status="PENDING",
    )
    db.add(email_q)

    print(
        f"[AUTOMATION] Programado email '{template_name}' para contacto {contact_id} "
        f"a las {scheduled_time.isoformat()} UTC"
    )


# =========================================================
# Motor principal de automatización
# =========================================================

def _update_lifecycle_stage(contact: Contact, now: datetime) -> None:
    """
    Actualiza la etapa del embudo (lifecycle_stage) de un contacto
    en función de sus datos y de la recencia de interacción.
    """
    # Si ya dejó correo y teléfono y tiene algo de engagement → lead_calificado
    if contact.email and contact.phone and (contact.engagement_score or 0) >= 5:
        if contact.lifecycle_stage == "nuevo_lead":
            contact.lifecycle_stage = "lead_calificado"

    # Si es lead calificado / cliente y lleva mucho sin interactuar → churn_risk
    if contact.lifecycle_stage in ("lead_calificado", "cliente"):
        if contact.last_interaction and contact.last_interaction < now - timedelta(days=30):
            contact.lifecycle_stage = "churn_risk"


def run_automation(db: Session) -> None:
    """
    Motor principal de automatización.
    Recorre todos los contactos y aplica reglas tipo Rappi/Amazon.

    Reglas actuales (MVP):
    - Regla 0: Actualizar lifecycle_stage (nuevo_lead → lead_calificado → churn_risk).
    - Regla 1: Enviar email de BIENVENIDA a contactos con engagement > 0 (solo una vez).
    - Regla 2: Enviar REENGANCHE si lleva 7 días sin interactuar.
    - Regla 3: Enviar PROFUNDIZACIÓN si tiene interés en educación + alto engagement.
    """

    now = datetime.utcnow()
    contactos = db.query(Contact).all()

    for c in contactos:
        score = c.engagement_score or 0

        # ---------------- Regla 0: lifecycle_stage ----------------
        _update_lifecycle_stage(c, now)

        # ---------------- Regla 1: Bienvenida ----------------
        # Cualquier contacto que ya tenga algo de interacción (likes, mensajes, etc.)
        # debería recibir una bienvenida, pero solo una vez en la vida.
        if score > 0:
            schedule_email(
                db=db,
                contact_id=c.id,
                template_name="bienvenida",
                delay_minutes=0,
                cooldown_days=365,  # prácticamente "solo una vez"
            )

        # ---------------- Regla 2: Reenganche ----------------
        # Si ha interactuado alguna vez, pero lleva 7 días o más sin hacerlo,
        # le mandamos un email de "Te extrañamos".
        if (
            score > 0
            and c.last_interaction
            and c.last_interaction < now - timedelta(days=7)
        ):
            schedule_email(
                db=db,
                contact_id=c.id,
                template_name="reenganche",
                delay_minutes=0,
                cooldown_days=7,
            )

        # ---------------- Regla 3: Profundización educación ----------------
        # Leads que:
        # - tienen buen engagement,
        # - y cuyo tema principal es "educacion",
        # reciben contenido más avanzado.
        if (
            score >= 15
            and c.main_topic == "educacion"
        ):
            schedule_email(
                db=db,
                contact_id=c.id,
                template_name="profundizacion_educacion",
                delay_minutes=0,
                cooldown_days=14,
            )

    # Un solo commit para todos los cambios de la corrida
    db.commit()
