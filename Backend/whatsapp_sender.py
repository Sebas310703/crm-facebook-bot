"""
whatsapp_sender.py — PolitiCRM
Integración con Meta WhatsApp Cloud API.

Funciones principales:
  - enviar_mensaje_whatsapp()  → envía un mensaje individual
  - enviar_masivo_whatsapp()   → envía mensajes masivos a líderes filtrados
  - verificar_configuracion()  → valida que las variables de entorno estén OK

Tipos de mensaje soportados:
  - Texto libre    → válido solo dentro de la ventana de 24h
  - Template Meta  → válido siempre (requiere plantilla aprobada por Meta)

Variables de entorno requeridas (.env):
  WA_PHONE_NUMBER_ID → ID del número registrado en Meta Business
  WA_ACCESS_TOKEN    → Token de acceso permanente o de sistema
  WA_API_VERSION     → Versión de la API (default: v19.0)
  WA_DELAY           → Pausa entre mensajes masivos en segundos (default: 1.2)
"""
import logging
import os
import time
from typing import Optional

import httpx
from dotenv import load_dotenv
from sqlalchemy.orm import Session

load_dotenv()

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s [WA] %(message)s")

# ================================================================
# CONFIGURACIÓN
# ================================================================

WA_PHONE_NUMBER_ID = os.getenv("WA_PHONE_NUMBER_ID")
WA_ACCESS_TOKEN    = os.getenv("WA_ACCESS_TOKEN")
WA_API_VERSION     = os.getenv("WA_API_VERSION", "v19.0")
WA_API_URL         = f"https://graph.facebook.com/{WA_API_VERSION}/{WA_PHONE_NUMBER_ID}/messages"

# Pausa entre mensajes para respetar el rate-limit de Meta (≥ 1s recomendado)
DELAY_ENTRE_MENSAJES = float(os.getenv("WA_DELAY", "1.2"))

# Validación temprana
if not WA_PHONE_NUMBER_ID:
    logger.warning("⚠️  WA_PHONE_NUMBER_ID no configurado — los envíos de WhatsApp fallarán")
if not WA_ACCESS_TOKEN:
    logger.warning("⚠️  WA_ACCESS_TOKEN no configurado — los envíos de WhatsApp fallarán")


# ================================================================
# HELPERS INTERNOS
# ================================================================

def _headers() -> dict:
    return {
        "Authorization": f"Bearer {WA_ACCESS_TOKEN}",
        "Content-Type":  "application/json",
    }


def _payload_texto(telefono_e164: str, mensaje: str) -> dict:
    """
    Payload para mensaje de texto libre.
    Solo válido dentro de la ventana de 24h tras la última interacción.
    """
    return {
        "messaging_product": "whatsapp",
        "recipient_type":    "individual",
        "to":                telefono_e164,
        "type":              "text",
        "text": {
            "preview_url": False,
            "body":        mensaje,
        },
    }


def _payload_template(
    telefono_e164: str,
    template_name: str,
    idioma: str = "es",
    componentes: Optional[list] = None,
) -> dict:
    """
    Payload para mensaje con plantilla aprobada por Meta.
    Usar este tipo fuera de la ventana de 24h.
    """
    payload = {
        "messaging_product": "whatsapp",
        "to":                telefono_e164,
        "type":              "template",
        "template": {
            "name":     template_name,
            "language": {"code": idioma},
        },
    }
    if componentes:
        payload["template"]["components"] = componentes
    return payload


def _manejar_respuesta(response: httpx.Response, telefono: str) -> dict:
    """
    Procesa la respuesta de la API de Meta y retorna un dict estandarizado.
    """
    try:
        data = response.json()
    except Exception:
        return {"ok": False, "error": f"Respuesta no JSON: {response.text}"}

    if response.status_code == 200 and "messages" in data:
        msg_id = data["messages"][0].get("id", "")
        logger.info(f"✓ Enviado a {telefono} | message_id={msg_id}")
        return {"ok": True, "message_id": msg_id}

    # Extraer error de Meta
    error_info  = data.get("error", {})
    error_msg   = error_info.get("message",       str(data))
    error_code  = error_info.get("code",          "")
    error_sub   = error_info.get("error_subcode", "")

    logger.warning(
        f"✗ Error enviando a {telefono} | "
        f"code={error_code} sub={error_sub} msg={error_msg}"
    )
    return {
        "ok":      False,
        "error":   error_msg,
        "code":    error_code,
        "subcode": error_sub,
    }


# ================================================================
# FUNCIÓN PRINCIPAL — enviar un mensaje individual
# ================================================================

def enviar_mensaje_whatsapp(
    telefono_e164: str,
    mensaje: str = None,
    template_name: str = None,
    template_componentes: list = None,
    idioma: str = "es",
) -> dict:
    """
    Envía un único mensaje de WhatsApp.

    Prioridad:
      1. Si se pasa template_name → envía plantilla (funciona siempre)
      2. Si se pasa mensaje       → envía texto libre (requiere ventana 24h)

    Args:
        telefono_e164:        Teléfono en formato E.164 (ej: +573001234567)
        mensaje:              Texto libre del mensaje
        template_name:        Nombre de plantilla aprobada en Meta
        template_componentes: Variables de la plantilla (opcional)
        idioma:               Código de idioma para templates (default: "es")

    Returns:
        Dict con {ok: bool, message_id: str} o {ok: False, error: str}
    """
    if not WA_ACCESS_TOKEN or not WA_PHONE_NUMBER_ID:
        return {"ok": False, "error": "WhatsApp no configurado — revisa WA_ACCESS_TOKEN y WA_PHONE_NUMBER_ID en .env"}

    if not telefono_e164:
        return {"ok": False, "error": "Teléfono vacío o inválido"}

    # Seleccionar tipo de payload
    if template_name:
        payload = _payload_template(
            telefono_e164,
            template_name,
            idioma=idioma,
            componentes=template_componentes,
        )
    elif mensaje:
        payload = _payload_texto(telefono_e164, mensaje)
    else:
        return {"ok": False, "error": "Debes proveer 'mensaje' o 'template_name'"}

    try:
        with httpx.Client(timeout=15) as client:
            response = client.post(
                WA_API_URL,
                json=payload,
                headers=_headers(),
            )
        return _manejar_respuesta(response, telefono_e164)

    except httpx.TimeoutException:
        logger.error(f"✗ Timeout enviando a {telefono_e164}")
        return {"ok": False, "error": "Timeout al conectar con Meta WhatsApp API"}
    except httpx.RequestError as exc:
        logger.error(f"✗ Error de conexión para {telefono_e164}: {exc}")
        return {"ok": False, "error": str(exc)}


# ================================================================
# ENVÍO MASIVO A LÍDERES
# ================================================================

def enviar_masivo_whatsapp(
    db: Session,
    mensaje: str = None,
    template_name: str = None,
    template_componentes: list = None,
    sector: str = None,
    limite: int = None,
    solo_activos: bool = True,
) -> dict:
    """
    Envía mensajes masivos de WhatsApp a los líderes registrados.

    Args:
        db:                   Sesión de SQLAlchemy activa.
        mensaje:              Texto libre (solo dentro de ventana 24h).
        template_name:        Plantilla aprobada por Meta (funciona siempre).
        template_componentes: Variables de la plantilla (opcional).
        sector:               Filtrar por nombre de barrio (opcional).
        limite:               Máximo de líderes a contactar (para pruebas).
        solo_activos:         Solo líderes con activo=True (default: True).

    Returns:
        Dict con resumen: {total, enviados, fallidos, omitidos, errores}
    """
    from lider_model import LiderSeguro

    # Construir query
    query = db.query(LiderSeguro).filter(LiderSeguro.telefono.isnot(None))

    if solo_activos:
        query = query.filter(LiderSeguro.activo == True)
    if sector:
        from lider_model import Barrio
        barrio = db.query(Barrio).filter(Barrio.nombre == sector.upper()).first()
        if barrio:
            query = query.filter(LiderSeguro.barrio_id == barrio.id)
        else:
            logger.warning(f"Barrio '{sector}' no encontrado — enviando a todos")
    if limite:
        query = query.limit(limite)

    lideres = query.all()
    total   = len(lideres)

    logger.info(
        f"Iniciando envío masivo WhatsApp → {total} líderes"
        f"{f' | sector={sector}' if sector else ''}"
        f"{f' | límite={limite}' if limite else ''}"
    )

    enviados = 0
    fallidos = 0
    omitidos = 0
    errores  = []

    for lider in lideres:
        telefono = lider.telefono_e164()

        if not telefono:
            logger.warning(f"Líder {lider.id} ({lider.nombre}) sin teléfono válido — omitiendo")
            omitidos += 1
            continue

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
            errores.append({
                "lider_id": lider.id,
                "nombre":   lider.nombre,
                "telefono": telefono,
                "error":    resultado.get("error"),
            })

        # Respetar rate-limit de Meta
        time.sleep(DELAY_ENTRE_MENSAJES)

    resumen = {
        "total":    total,
        "enviados": enviados,
        "fallidos": fallidos,
        "omitidos": omitidos,
        "errores":  errores,
    }
    logger.info(
        f"✓ Envío masivo finalizado: "
        f"{enviados}/{total} exitosos | "
        f"{fallidos} fallidos | "
        f"{omitidos} omitidos"
    )
    return resumen


# ================================================================
# VERIFICACIÓN DE CONFIGURACIÓN
# ================================================================

def verificar_configuracion() -> dict:
    """
    Verifica que las variables de entorno de WhatsApp estén configuradas
    y que la conexión con Meta sea posible.

    Returns:
        Dict con estado de la configuración.
    """
    config = {
        "WA_PHONE_NUMBER_ID": bool(WA_PHONE_NUMBER_ID),
        "WA_ACCESS_TOKEN":    bool(WA_ACCESS_TOKEN),
        "WA_API_VERSION":     WA_API_VERSION,
        "WA_API_URL":         WA_API_URL,
        "DELAY_ENTRE_MENSAJES": DELAY_ENTRE_MENSAJES,
    }

    if not WA_PHONE_NUMBER_ID or not WA_ACCESS_TOKEN:
        config["estado"] = "❌ Configuración incompleta — revisa .env"
        config["ok"]     = False
        return config

    # Verificar conectividad con Meta
    try:
        with httpx.Client(timeout=10) as client:
            response = client.get(
                f"https://graph.facebook.com/{WA_API_VERSION}/{WA_PHONE_NUMBER_ID}",
                headers=_headers(),
            )
        if response.status_code == 200:
            config["estado"] = "✅ Conexión con Meta exitosa"
            config["ok"]     = True
        else:
            data = response.json()
            config["estado"] = f"⚠️  Meta respondió con error: {data.get('error', {}).get('message', response.text)}"
            config["ok"]     = False

    except httpx.RequestError as exc:
        config["estado"] = f"❌ Error de conexión: {exc}"
        config["ok"]     = False

    return config