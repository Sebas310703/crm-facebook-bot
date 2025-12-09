import os
import requests

FACEBOOK_PAGE_TOKEN = os.getenv("FACEBOOK_PAGE_ACCESS_TOKEN")
print("[DEBUG] TOKEN CARGADO:", FACEBOOK_PAGE_TOKEN is not None)


def send_facebook_message(psid: str, text: str):
    """
    Envía un mensaje de texto a un usuario de Facebook Messenger
    usando la Graph API.

    psid = Page Scoped ID del usuario (sender.id en los eventos).
    """
    if not FACEBOOK_PAGE_TOKEN:
        print("[FB] No hay FACEBOOK_PAGE_ACCESS_TOKEN configurado.")
        return

    url = "https://graph.facebook.com/v20.0/me/messages"
    params = {"access_token": FACEBOOK_PAGE_TOKEN}
    payload = {
        "recipient": {"id": psid},
        "message": {"text": text}
    }

    try:
        r = requests.post(url, json=payload, params=params)
        print("[FB] Respuesta:", r.status_code, r.text)
    except Exception as e:
        print("[FB] Error enviando mensaje:", e)
