"""
facebook_api.py — PolitiCRM
Integración con Meta Graph API.

Funciones:
  - send_facebook_message()       → envía mensaje por Messenger
  - send_facebook_private_reply() → responde privadamente a un comentario de post
  - get_user_profile()            → obtiene nombre y foto del usuario por PSID

Variables de entorno requeridas (.env):
  FACEBOOK_PAGE_ACCESS_TOKEN  → token de página de Meta
  FACEBOOK_API_VERSION        → versión de la API (default: v20.0)
"""
import os
import logging

import requests
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s [FB] %(message)s")

# ── Configuración ─────────────────────────────────────────
FACEBOOK_PAGE_TOKEN = os.getenv("FACEBOOK_PAGE_ACCESS_TOKEN")
FACEBOOK_API_VERSION = os.getenv("FACEBOOK_API_VERSION", "v20.0")
GRAPH_BASE_URL = f"https://graph.facebook.com/{FACEBOOK_API_VERSION}"

if not FACEBOOK_PAGE_TOKEN:
    logger.warning("⚠️  FACEBOOK_PAGE_ACCESS_TOKEN no configurado — los envíos a FB fallarán")


# =========================================================
# HELPERS INTERNOS
# =========================================================

def _headers() -> dict:
    return {"Content-Type": "application/json"}


def _params() -> dict:
    return {"access_token": FACEBOOK_PAGE_TOKEN}


def _log_response(response: requests.Response, context: str) -> bool:
    """Loguea la respuesta y retorna True si fue exitosa."""
    if response.status_code == 200:
        logger.info(f"✓ [{context}] Enviado correctamente | {response.status_code}")
        return True
    else:
        logger.warning(
            f"✗ [{context}] Error {response.status_code}: {response.text}"
        )
        return False


# =========================================================
# ENVIAR MENSAJE POR MESSENGER
# =========================================================

def send_facebook_message(psid: str, text: str) -> bool:
    """
    Envía un mensaje de texto a un usuario de Facebook Messenger.

    Args:
        psid: Page Scoped ID del usuario (sender.id en los eventos del webhook).
        text: Texto del mensaje a enviar.

    Returns:
        True si el envío fue exitoso, False en caso contrario.
    """
    if not FACEBOOK_PAGE_TOKEN:
        logger.error("[send_facebook_message] No hay token configurado.")
        return False

    if not psid or not text:
        logger.error("[send_facebook_message] psid y text son requeridos.")
        return False

    url = f"{GRAPH_BASE_URL}/me/messages"
    payload = {
        "recipient": {"id": psid},
        "message":   {"text": text},
        "messaging_type": "RESPONSE",
    }

    try:
        response = requests.post(
            url,
            json=payload,
            params=_params(),
            headers=_headers(),
            timeout=10,
        )
        return _log_response(response, "Messenger")

    except requests.exceptions.Timeout:
        logger.error("[send_facebook_message] Timeout al conectar con Meta.")
        return False
    except requests.exceptions.RequestException as e:
        logger.error(f"[send_facebook_message] Error de conexión: {e}")
        return False


# =========================================================
# RESPUESTA PRIVADA A COMENTARIO DE POST
# =========================================================

def send_facebook_private_reply(comment_id: str, text: str) -> bool:
    """
    Envía una respuesta privada (Private Reply) a un comentario de un post.
    El usuario recibe el mensaje en su bandeja de Messenger.

    Requisito: La página debe tener permiso 'pages_messaging' y
               'pages_read_engagement' aprobados en Meta.

    Args:
        comment_id: ID del comentario al que se responde.
        text:       Texto de la respuesta privada.

    Returns:
        True si el envío fue exitoso, False en caso contrario.
    """
    if not FACEBOOK_PAGE_TOKEN:
        logger.error("[send_facebook_private_reply] No hay token configurado.")
        return False

    if not comment_id or not text:
        logger.error("[send_facebook_private_reply] comment_id y text son requeridos.")
        return False

    url = f"{GRAPH_BASE_URL}/me/messages"
    payload = {
        "recipient":      {"comment_id": comment_id},
        "message":        {"text": text},
        "messaging_type": "RESPONSE",
    }

    try:
        response = requests.post(
            url,
            json=payload,
            params=_params(),
            headers=_headers(),
            timeout=10,
        )
        return _log_response(response, "PrivateReply")

    except requests.exceptions.Timeout:
        logger.error("[send_facebook_private_reply] Timeout al conectar con Meta.")
        return False
    except requests.exceptions.RequestException as e:
        logger.error(f"[send_facebook_private_reply] Error de conexión: {e}")
        return False


# =========================================================
# OBTENER PERFIL DEL USUARIO
# =========================================================

def get_user_profile(psid: str) -> dict | None:
    """
    Obtiene el nombre y foto de perfil de un usuario por su PSID.
    Útil para guardar el nombre real del contacto al registrarlo.

    Args:
        psid: Page Scoped ID del usuario.

    Returns:
        Dict con 'first_name', 'last_name', 'profile_pic' o None si falla.
    """
    if not FACEBOOK_PAGE_TOKEN:
        logger.error("[get_user_profile] No hay token configurado.")
        return None

    if not psid:
        return None

    url = f"{GRAPH_BASE_URL}/{psid}"
    params = {
        **_params(),
        "fields": "first_name,last_name,profile_pic",
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            logger.info(f"✓ [get_user_profile] Perfil obtenido para PSID {psid}")
            return {
                "first_name":   data.get("first_name", ""),
                "last_name":    data.get("last_name", ""),
                "full_name":    f"{data.get('first_name', '')} {data.get('last_name', '')}".strip(),
                "profile_pic":  data.get("profile_pic"),
            }
        else:
            logger.warning(f"✗ [get_user_profile] Error {response.status_code}: {response.text}")
            return None

    except requests.exceptions.RequestException as e:
        logger.error(f"[get_user_profile] Error de conexión: {e}")
        return None


# =========================================================
# ENVIAR MENSAJE CON BOTONES (Quick Replies)
# =========================================================

def send_quick_replies(psid: str, text: str, options: list[str]) -> bool:
    """
    Envía un mensaje con botones de respuesta rápida (Quick Replies).
    Máximo 13 opciones según la API de Meta.

    Args:
        psid:    Page Scoped ID del usuario.
        text:    Texto del mensaje.
        options: Lista de textos para los botones (máx 13, máx 20 chars c/u).

    Returns:
        True si el envío fue exitoso, False en caso contrario.

    Ejemplo:
        send_quick_replies(psid, "¿Qué tema te interesa?", ["Educación", "Empleo", "Salud"])
    """
    if not FACEBOOK_PAGE_TOKEN:
        logger.error("[send_quick_replies] No hay token configurado.")
        return False

    quick_replies = [
        {
            "content_type": "text",
            "title": opt[:20],   # Meta limita a 20 caracteres
            "payload": opt.upper().replace(" ", "_"),
        }
        for opt in options[:13]  # Meta limita a 13 opciones
    ]

    url = f"{GRAPH_BASE_URL}/me/messages"
    payload = {
        "recipient": {"id": psid},
        "message": {
            "text": text,
            "quick_replies": quick_replies,
        },
        "messaging_type": "RESPONSE",
    }

    try:
        response = requests.post(
            url,
            json=payload,
            params=_params(),
            headers=_headers(),
            timeout=10,
        )
        return _log_response(response, "QuickReplies")

    except requests.exceptions.RequestException as e:
        logger.error(f"[send_quick_replies] Error de conexión: {e}")
        return False