"""
email_sender.py — PolitiCRM
Motor de envío de emails.

Dos modos de operación:
  1. SIMULADO (default)  → imprime en consola, no requiere configuración SMTP
  2. SMTP REAL           → configura las variables SMTP_* en .env

Variables de entorno opcionales (.env):
  SMTP_HOST      → servidor SMTP     (ej: smtp.gmail.com)
  SMTP_PORT      → puerto SMTP       (default: 587)
  SMTP_USER      → usuario/correo    (ej: tucorreo@gmail.com)
  SMTP_PASSWORD  → contraseña o app password
  SMTP_FROM      → remitente         (ej: campaña@politicrm.com)
  SMTP_USE_TLS   → usar TLS          (default: true)

Si SMTP_HOST no está configurado, el sistema opera en modo simulado.
"""
import logging
import os
import smtplib
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from sqlalchemy.orm import Session

from models import Contact, EmailQueue, EmailTemplate

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s [EMAIL] %(message)s")

# =========================================================
# CONFIGURACIÓN SMTP DESDE .env
# =========================================================

SMTP_HOST     = os.getenv("SMTP_HOST")
SMTP_PORT     = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER     = os.getenv("SMTP_USER")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
SMTP_FROM     = os.getenv("SMTP_FROM", SMTP_USER or "noreply@politicrm.com")
SMTP_USE_TLS  = os.getenv("SMTP_USE_TLS", "true").lower() == "true"

# Modo simulado si no hay SMTP configurado
MODO_SIMULADO = not SMTP_HOST

if MODO_SIMULADO:
    logger.info("📧 Email sender en MODO SIMULADO — configura SMTP_HOST en .env para envío real")
else:
    logger.info(f"📧 Email sender configurado → {SMTP_HOST}:{SMTP_PORT} desde {SMTP_FROM}")


# =========================================================
# HELPER — construir mensaje MIME
# =========================================================

def _build_email(
    to_email: str,
    subject: str,
    body: str,
    contact_name: str = "",
) -> MIMEMultipart:
    """
    Construye el objeto MIMEMultipart con cabeceras y cuerpo del email.
    Soporta texto plano y HTML básico.
    """
    msg = MIMEMultipart("alternative")
    msg["From"]    = SMTP_FROM
    msg["To"]      = to_email
    msg["Subject"] = subject

    # Personalizar cuerpo con nombre si está disponible
    saludo = f"Hola {contact_name.title()},\n\n" if contact_name else ""
    cuerpo_texto = saludo + body

    # Versión texto plano
    part_text = MIMEText(cuerpo_texto, "plain", "utf-8")

    # Versión HTML básica
    html_body = cuerpo_texto.replace("\n", "<br>")
    part_html = MIMEText(
        f"<html><body><p>{html_body}</p></body></html>",
        "html",
        "utf-8",
    )

    msg.attach(part_text)
    msg.attach(part_html)
    return msg


# =========================================================
# ENVÍO REAL VÍA SMTP
# =========================================================

def _send_via_smtp(to_email: str, subject: str, body: str, contact_name: str = "") -> bool:
    """
    Envía un email real usando SMTP.

    Returns:
        True si fue exitoso, False si falló.
    """
    try:
        msg = _build_email(to_email, subject, body, contact_name)

        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=10) as server:
            if SMTP_USE_TLS:
                server.starttls()
            if SMTP_USER and SMTP_PASSWORD:
                server.login(SMTP_USER, SMTP_PASSWORD)
            server.sendmail(SMTP_FROM, to_email, msg.as_string())

        logger.info(f"✓ Email enviado a {to_email} | Asunto: {subject}")
        return True

    except smtplib.SMTPAuthenticationError:
        logger.error(f"✗ Error de autenticación SMTP para {to_email}")
        return False
    except smtplib.SMTPRecipientsRefused:
        logger.error(f"✗ Destinatario rechazado: {to_email}")
        return False
    except smtplib.SMTPException as e:
        logger.error(f"✗ Error SMTP enviando a {to_email}: {e}")
        return False
    except Exception as e:
        logger.error(f"✗ Error inesperado enviando a {to_email}: {e}")
        return False


# =========================================================
# ENVÍO SIMULADO (consola)
# =========================================================

def _send_simulated(
    contact_id: int,
    to_email: str | None,
    subject: str,
    body: str,
    contact_name: str = "",
    queue_id: int = 0,
) -> bool:
    """
    Simula el envío imprimiendo en consola.
    No requiere configuración SMTP.
    """
    saludo = f"Hola {contact_name.title()},\n\n" if contact_name else ""
    print("\n" + "=" * 55)
    print(f"  📧 EMAIL SIMULADO")
    print("=" * 55)
    print(f"  Queue ID   : {queue_id}")
    print(f"  Contacto   : {contact_id} ({contact_name or 'Sin nombre'})")
    print(f"  Para       : {to_email or '⚠️  Sin email registrado'}")
    print(f"  Asunto     : {subject}")
    print(f"  Cuerpo     :")
    print(f"  {saludo}{body}")
    print("=" * 55 + "\n")
    return True


# =========================================================
# FUNCIÓN PRINCIPAL — enviar emails pendientes
# =========================================================

def send_pending_emails(db: Session, limit: int = 100) -> dict:
    """
    Procesa y envía todos los emails en estado PENDING.

    Args:
        db:    Sesión de SQLAlchemy.
        limit: Máximo de emails a procesar por ejecución (default: 100).

    Returns:
        Dict con resumen: enviados, fallidos, omitidos (sin email).
    """
    pendientes = (
        db.query(EmailQueue)
        .filter_by(status="PENDING")
        .order_by(EmailQueue.scheduled_at)
        .limit(limit)
        .all()
    )

    if not pendientes:
        logger.info("Sin emails pendientes en este ciclo")
        return {"enviados": 0, "fallidos": 0, "omitidos": 0}

    logger.info(f"Procesando {len(pendientes)} emails pendientes...")

    enviados = 0
    fallidos = 0
    omitidos = 0

    for e in pendientes:
        # Cargar plantilla y contacto
        template = db.get(EmailTemplate, e.template_id)
        contact  = db.get(Contact, e.contact_id)

        if not template:
            logger.warning(f"Plantilla {e.template_id} no encontrada — omitiendo queue {e.id}")
            e.status    = "FAILED"
            e.error_msg = "Plantilla no encontrada"
            fallidos += 1
            db.commit()
            continue

        if not contact:
            logger.warning(f"Contacto {e.contact_id} no encontrado — omitiendo queue {e.id}")
            e.status    = "FAILED"
            e.error_msg = "Contacto no encontrado"
            fallidos += 1
            db.commit()
            continue

        # Si el contacto no tiene email, marcar como omitido
        if not contact.email:
            logger.info(
                f"Contacto {contact.id} sin email registrado "
                f"— omitiendo '{template.name}'"
            )
            e.status    = "FAILED"
            e.error_msg = "Contacto sin email registrado"
            omitidos += 1
            db.commit()
            continue

        # Enviar según el modo configurado
        if MODO_SIMULADO:
            ok = _send_simulated(
                contact_id=contact.id,
                to_email=contact.email,
                subject=template.subject,
                body=template.body,
                contact_name=contact.full_name or "",
                queue_id=e.id,
            )
        else:
            ok = _send_via_smtp(
                to_email=contact.email,
                subject=template.subject,
                body=template.body,
                contact_name=contact.full_name or "",
            )

        # Actualizar estado en la cola
        if ok:
            e.status  = "SENT"
            e.sent_at = datetime.utcnow()
            enviados += 1
        else:
            e.status    = "FAILED"
            e.error_msg = "Error en el envío SMTP"
            fallidos += 1

        db.commit()

    resumen = {"enviados": enviados, "fallidos": fallidos, "omitidos": omitidos}
    logger.info(f"✓ Ciclo email completo: {resumen}")
    return resumen


# =========================================================
# ENVÍO INDIVIDUAL — para pruebas o casos especiales
# =========================================================

def send_single_email(
    db: Session,
    contact_id: int,
    template_name: str,
) -> dict:
    """
    Envía un email inmediato a un contacto específico sin pasar por la cola.
    Útil para pruebas o envíos urgentes.

    Args:
        db:            Sesión de SQLAlchemy.
        contact_id:    ID del contacto destino.
        template_name: Nombre de la plantilla a usar.

    Returns:
        Dict con resultado del envío.
    """
    contact  = db.get(Contact, contact_id)
    template = db.query(EmailTemplate).filter_by(name=template_name).first()

    if not contact:
        return {"ok": False, "error": "Contacto no encontrado"}
    if not template:
        return {"ok": False, "error": f"Plantilla '{template_name}' no encontrada"}
    if not contact.email:
        return {"ok": False, "error": "El contacto no tiene email registrado"}

    if MODO_SIMULADO:
        ok = _send_simulated(
            contact_id=contact.id,
            to_email=contact.email,
            subject=template.subject,
            body=template.body,
            contact_name=contact.full_name or "",
        )
    else:
        ok = _send_via_smtp(
            to_email=contact.email,
            subject=template.subject,
            body=template.body,
            contact_name=contact.full_name or "",
        )

    return {
        "ok": ok,
        "contact_id": contact_id,
        "email": contact.email,
        "template": template_name,
        "modo": "simulado" if MODO_SIMULADO else "smtp_real",
    }