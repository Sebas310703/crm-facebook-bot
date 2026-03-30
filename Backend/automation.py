from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from models import Contact, EmailTemplate, EmailQueue


def schedule_email(db: Session, contact_id: int, template_name: str):
    """
    Crea un registro en la cola de emails si no existe uno pendiente
    para ese contacto y esa plantilla.
    """
    template = db.query(EmailTemplate).filter_by(name=template_name).first()
    if not template:
        print(f"[AUTOMATION] Plantilla '{template_name}' no existe")
        return

    already_pending = (
        db.query(EmailQueue)
        .filter_by(contact_id=contact_id, template_id=template.id, status="PENDING")
        .first()
    )

    if already_pending:
        return

    email_q = EmailQueue(
        contact_id=contact_id,
        template_id=template.id,
        scheduled_at=datetime.utcnow(),
        status="PENDING"
    )

    db.add(email_q)
    db.commit()
    print(f"[AUTOMATION] Programado email '{template_name}' para contacto {contact_id}")


def run_automation(db: Session):
    """
    Motor principal de automatización.
    Recorre todos los contactos y aplica reglas tipo Amazon.
    """
    now = datetime.utcnow()
    contactos = db.query(Contact).all()

    for c in contactos:
        # REGLA 1: Bienvenida si tiene engagement > 0
        if c.engagement_score > 0:
            schedule_email(db, c.id, "bienvenida")

        # REGLA 2: Reenganche si lleva 7 días sin interactuar
        if (
            c.engagement_score > 0
            and c.last_interaction < now - timedelta(days=7)
        ):
            schedule_email(db, c.id, "reenganche")

        # REGLA 3: Profundización por tema educación
        if (
            c.engagement_score >= 15
            and c.main_topic == "educacion"
        ):
            schedule_email(db, c.id, "profundizacion_educacion")
