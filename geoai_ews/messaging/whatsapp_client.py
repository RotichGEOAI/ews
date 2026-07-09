"""
WhatsApp Business Cloud API client (Meta).

CREDENTIALS REQUIRED (CREDENTIALS_AND_ACCESS_REQUIRED.pdf):
  - META_WHATSAPP_PHONE_NUMBER_ID
  - META_WHATSAPP_BUSINESS_ACCOUNT_ID
  - META_WHATSAPP_ACCESS_TOKEN
  - META_APP_ID / META_APP_SECRET (app-level, for token refresh / webhooks)
"""
from __future__ import annotations

import logging

import requests

from config.settings import settings

logger = logging.getLogger(__name__)

GRAPH_API_BASE = "https://graph.facebook.com/v19.0"


class WhatsAppClient:
    def __init__(self):
        if not (settings.meta_whatsapp_phone_number_id and settings.meta_whatsapp_access_token):
            raise EnvironmentError(
                "META_WHATSAPP_PHONE_NUMBER_ID / META_WHATSAPP_ACCESS_TOKEN not set. "
                "Register a Meta App + WhatsApp Business product to obtain these."
            )
        self.phone_number_id = settings.meta_whatsapp_phone_number_id
        self.access_token = settings.meta_whatsapp_access_token

    def send_text_message(self, to_phone_e164: str, message: str) -> dict:
        url = f"{GRAPH_API_BASE}/{self.phone_number_id}/messages"
        headers = {"Authorization": f"Bearer {self.access_token}"}
        payload = {
            "messaging_product": "whatsapp",
            "to": to_phone_e164,
            "type": "text",
            "text": {"body": message},
        }
        resp = requests.post(url, headers=headers, json=payload, timeout=30)
        resp.raise_for_status()
        logger.info("WhatsApp message sent to %s", to_phone_e164)
        return resp.json()
