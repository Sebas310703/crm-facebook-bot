from sqlalchemy.orm import Session
from models import EmailQueue, EmailTemplate

def send_pending_emails(db: Session):
    """
    Simula el envío de todos los emails en estado PENDING.
    No usa un servidor real de correo: solo imprime en consola
    y marca los correos como SENT.
    """
    pendientes = (
        db.query(EmailQueue)
        .filter_by(status="PENDING")
        .all()
    )

    enviados = 0

    for e in pendientes:
        template = db.query(EmailTemplate).filter_by(id=e.template_id).first()

        # Aquí podrías integrar un SMTP real.
        # Por ahora solo mostramos en consola:
        print("============== EMAIL ENVIADO ==============")
        print(f"EmailQueue ID: {e.id}")
        print(f"Contacto ID : {e.contact_id}")
        print(f"Asunto      : {template.subject}")
        print(f"Cuerpo      : {template.body}")
        print("===========================================")

        e.status = "SENT"
        enviados += 1

    db.commit()
    return enviados
