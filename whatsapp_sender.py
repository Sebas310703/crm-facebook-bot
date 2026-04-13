"""
whatsapp_sender.py
Envío masivo de mensajes WhatsApp a los líderes usando Meta Cloud API.

Requisitos en .env:
    WA_PHONE_NUMBER_ID=<tu phone_number_id del panel Meta>
    WA_ACCESS_TOKEN=<tu token permanente o de sistema>
    WA_API_VERSION=v19.0  (opcional, default v19.0)
"""
import os
import time
import logging
from typing import Optional

import httpx
from dotenv import load_dotenv
from sqlalchemy.orm import Session

from lider_model import Lider

load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(asctime)s [WA] %(message)s")
logger = logging.getLogger(__name__)

WA_PHONE_NUMBER_ID = os.getenv("WA_PHONE_NUMBER_ID")
WA_ACCESS_TOKEN = os.getenv("WA_ACCESS_TOKEN")
WA_API_VERSION = os.getenv("WA_API_VERSION", "v19.0")
WA_API_URL = f"https://graph.facebook.com/{WA_API_VERSION}/{WA_PHONE_NUMBER_ID}/messages"

# Pausa entre mensajes para respetar el rate-limit de Meta (recomendado ≥1 s)
DELAY_ENTRE_MENSAJES = float(os.getenv("WA_DELAY", "1.2"))


def _construir_payload_texto(telefono_e164: str, mensaje: str) -> dict:
    """Payload para mensaje de texto libre (solo válido dentro de ventana de 24 h)."""
    return {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": telefono_e164,
        "type": "text",
        "text": {"preview_url": False, "body": mensaje},
    }


def _construir_payload_template(
    telefono_e164: str,
    template_name: str,
    idioma: str = "es",
    componentes: Optional[list] = None,
) -> dict:
    """
    Payload para mensaje con plantilla aprobada por Meta.
    Usar este tipo fuera de la ventana de 24 h.
    """
    payload = {
        "messaging_product": "whatsapp",
        "to": telefono_e164,
        "type": "template",
        "template": {
            "name": template_name,
            "language": {"code": idioma},
        },
    }
    if componentes:
        payload["template"]["components"] = componentes
    return payload


def enviar_mensaje_whatsapp(
    telefono_e164: str,
    mensaje: str = None,
    template_name: str = None,
    template_componentes: list = None,
) -> dict:
    """
    Envía un único mensaje WhatsApp.
    - Si se pasa `mensaje`, envía texto libre (requiere ventana activa de 24 h).
    - Si se pasa `template_name`, envía plantilla aprobada (funciona siempre).
    Retorna {'ok': bool, 'message_id': str, 'error': str}
    """
    if template_name:
        payload = _construir_payload_template(
            telefono_e164, template_name, componentes=template_componentes
        )
    elif mensaje:
        payload = _construir_payload_texto(telefono_e164, mensaje)
    else:
        return {"ok": False, "error": "Debe proveer 'mensaje' o 'template_name'"}

    headers = {
        "Authorization": f"Bearer {WA_ACCESS_TOKEN}",
        "Content-Type": "application/json",
    }

    try:
        resp = httpx.post(WA_API_URL, json=payload, headers=headers, timeout=15)
        data = resp.json()

        if resp.status_code == 200 and "messages" in data:
            msg_id = data["messages"][0]["id"]
            logger.info(f"✓ Enviado a {telefono_e164} | id={msg_id}")
            return {"ok": True, "message_id": msg_id}
        else:
            error_msg = data.get("error", {}).get("message", str(data))
            error_sub = data.get("error", {}).get("error_subcode", "")
            logger.warning(f"✗ Error {telefono_e164} | {error_msg} (subcode={error_sub})")
            return {"ok": False, "error": error_msg, "subcode": error_sub}

    except httpx.RequestError as exc:
        logger.error(f"✗ Conexión fallida para {telefono_e164}: {exc}")
        return {"ok": False, "error": str(exc)}


def enviar_masivo_whatsapp(
    db: Session,
    mensaje: str = None,
    template_name: str = None,
    template_componentes: list = None,
    sector: str = None,
    limite: int = None,
) -> dict:
    """
    Envía mensajes masivos a todos los líderes (o filtrados por sector).

    Parámetros:
        db                   : Sesión SQLAlchemy activa
        mensaje              : Texto libre (solo si hay ventana 24 h abierta)
        template_name        : Nombre de plantilla Meta aprobada
        template_componentes : Variables de la plantilla (opcional)
        sector               : Filtrar por sector específico (opcional)
        limite               : Máximo de contactos a procesar (para pruebas)

    Retorna resumen: {'total': int, 'enviados': int, 'fallidos': int, 'errores': list}
    """
    query = db.query(Lider).filter(Lider.telefono.isnot(None))
    if sector:
        query = query.filter(Lider.sector == sector)
    if limite:
        query = query.limit(limite)

    lideres = query.all()
    total = len(lideres)
    logger.info(f"Iniciando envío masivo WhatsApp → {total} contactos")

    enviados, fallidos, errores = 0, 0, []

    for lider in lideres:
        telefono = lider.telefono_e164()
        resultado = enviar_mensaje_whatsapp(
            telefono_e164=telefono,
            mensaje=mensaje,
            template_name=template_name,
            template_componentes=template_componentes,
        )
        if resultado["ok"]:
            enviados += 1
        else:
            fallidos += 1
            errores.append({"nombre": lider.nombre, "telefono": telefono, "error": resultado.get("error")})

        time.sleep(DELAY_ENTRE_MENSAJES)

    resumen = {"total": total, "enviados": enviados, "fallidos": fallidos, "errores": errores}
    logger.info(f"Envío finalizado: {enviados}/{total} exitosos, {fallidos} fallidos")
    return resumen