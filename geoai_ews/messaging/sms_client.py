"""
SMS / alternate WhatsApp delivery via Twilio.

CREDENTIALS REQUIRED (CREDENTIALS_AND_ACCESS_REQUIRED.pdf):
  - TWILIO_ACCOUNT_SID
  - TWILIO_AUTH_TOKEN
  - TWILIO_FROM_NUMBER
"""
from __future__ import annotations

import logging

from config.settings import settings

logger = logging.getLogger(__name__)


class SmsClient:
    def __init__(self):
        if not (settings.twilio_account_sid and settings.twilio_auth_token and settings.twilio_from_number):
            raise EnvironmentError(
                "TWILIO_ACCOUNT_SID / TWILIO_AUTH_TOKEN / TWILIO_FROM_NUMBER not set. "
                "Create a Twilio account and provision a sending number/WhatsApp sender."
            )
        from twilio.rest import Client

        self.client = Client(settings.twilio_account_sid, settings.twilio_auth_token)
        self.from_number = settings.twilio_from_number

    def send_sms(self, to_phone_e164: str, message: str) -> dict:
        msg = self.client.messages.create(body=message, from_=self.from_number, to=to_phone_e164)
        logger.info("SMS sent to %s (sid=%s)", to_phone_e164, msg.sid)
        return {"sid": msg.sid, "status": msg.status}
