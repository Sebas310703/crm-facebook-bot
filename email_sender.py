from datetime import datetime
from sqlalchemy.orm import Session

from models import EmailQueue, EmailTemplate


def send_pending_emails(db: Session) -> int:
    """
    Simula el envío de todos los emails en estado PENDING.
    Más adelante aquí se puede integrar un servidor SMTP real.
    
    Flujo:
    1. Busca todos los emails pendientes.
    2. Obtiene su plantilla.
    3. "Envía" (simulado).
    4. Marca como SENT + guarda sent_at.
    """

    pendientes = (
        db.query(EmailQueue)
        .filter_by(status="PENDING")
        .all()
    )

    enviados = 0

    if not pendientes:
        print("[EMAIL] No hay correos pendientes para enviar.")
        return 0

    print(f"[EMAIL] Iniciando envío de {len(pendientes)} correos pendientes...\n")

    for e in pendientes:
        template = (
            db.query(EmailTemplate)
            .filter_by(id=e.template_id)
            .first()
        )

        if not template:
            print(f"[EMAIL][ERROR] No se encontró plantilla para EmailQueue ID {e.id}")
            continue

        # ===================== ENVÍO SIMULADO =====================
        print("============== EMAIL ENVIADO ==============")
        print(f"EmailQueue ID : {e.id}")
        print(f"Contacto ID   : {e.contact_id}")
        print(f"Asunto        : {template.subject}")
        print(f"Cuerpo        : {template.body}")
        print(f"Enviado en    : {datetime.utcnow().isoformat()} UTC")
        print("===========================================\n")
        # ==========================================================

        # Marcar como enviado
        e.status = "SENT"
        e.sent_at = datetime.utcnow()

        enviados += 1

    db.commit()

    print(f"[EMAIL] Envío finalizado. Total enviados: {enviados}")
    return enviados
