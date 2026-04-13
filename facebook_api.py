import os
import requests
from typing import Any, Dict

# =========================================================
# CONFIG
# =========================================================

FACEBOOK_PAGE_TOKEN = os.getenv("FACEBOOK_PAGE_ACCESS_TOKEN")

if FACEBOOK_PAGE_TOKEN:
    print("[FB][INIT] Page Access Token cargado correctamente.")
else:
    print("[FB][WARN] FACEBOOK_PAGE_ACCESS_TOKEN no está configurado. No se podrán enviar mensajes.")


# =========================================================
# FUNCIONES BASE
# =========================================================

def _call_facebook_send_api(payload: Dict[str, Any]) -> None:
    """
    Llama a la Graph API de Facebook para enviar mensajes a Messenger.
    Esta función es el núcleo: send_facebook_message solo construye el payload
    y se lo pasa.
    """
    if not FACEBOOK_PAGE_TOKEN:
        print("[FB][ERROR] No hay FACEBOOK_PAGE_ACCESS_TOKEN configurado.")
        return

    url = "https://graph.facebook.com/v20.0/me/messages"
    params = {"access_token": FACEBOOK_PAGE_TOKEN}

    try:
        response = requests.post(url, json=payload, params=params, timeout=10)
    except Exception as e:
        print(f"[FB][ERROR] Error de red enviando mensaje: {e}")
        return

    if not response.ok:
        print(
            f"[FB][ERROR] Fallo al enviar mensaje. "
            f"Status: {response.status_code}, Respuesta: {response.text}"
        )
        return

    print("[FB][OK] Mensaje enviado correctamente:", response.text)


# =========================================================
# API PÚBLICA
# =========================================================

def send_facebook_message(psid: str, text: str) -> None:
    """
    Envía un mensaje de texto a un usuario de Facebook Messenger usando la Graph API.

    psid: Page Scoped ID del usuario (sender.id en los eventos).
    text: texto plano a enviar.
    """
    if not psid:
        print("[FB][WARN] PSID vacío, no se envía mensaje.")
        return

    payload = {
        "recipient": {"id": psid},
        "message": {"text": text},
    }

    _call_facebook_send_api(payload)


def send_facebook_private_reply(comment_id: str, text: str) -> None:
    """
    Envía un mensaje privado en respuesta a un comentario de Facebook.
    comment_id: ID del comentario al que se responde.
    text: texto a enviar.
    """
    if not FACEBOOK_PAGE_TOKEN:
        print("[FB][ERROR] No hay FACEBOOK_PAGE_ACCESS_TOKEN configurado.")
        return

    url = f"https://graph.facebook.com/v20.0/{comment_id}/private_replies"
    params = {"access_token": FACEBOOK_PAGE_TOKEN}
    payload = {"message": text}

    try:
        response = requests.post(url, json=payload, params=params, timeout=10)
    except Exception as e:
        print(f"[FB][ERROR] Error de red enviando private reply: {e}")
        return

    if not response.ok:
        print(
            f"[FB][ERROR] Fallo al enviar private reply. "
            f"Status: {response.status_code}, Respuesta: {response.text}"
        )
        return

    print("[FB][OK] Private reply enviado correctamente:", response.text)