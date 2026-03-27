from __future__ import annotations

import asyncio
import logging
from typing import Any, Dict

import httpx

from senior_health.config import Settings

logger = logging.getLogger(__name__)


class WhatsAppClient:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    async def send_text(self, to_phone: str, text: str) -> Dict[str, Any]:
        if not self.settings.access_token or not self.settings.phone_number_id:
            logger.error("ACCESS_TOKEN or PHONE_NUMBER_ID not configured")
            return {"error": "missing_credentials"}

        to_phone = "".join(ch for ch in str(to_phone) if ch.isdigit())
        if not to_phone:
            return {"error": "invalid_to_phone"}

        url = (
            f"https://graph.facebook.com/{self.settings.graph_api_version}/"
            f"{self.settings.phone_number_id}/messages"
        )
        headers = {
            "Authorization": f"Bearer {self.settings.access_token}",
            "Content-Type": "application/json",
        }
        payload = {
            "messaging_product": "whatsapp",
            "to": to_phone,
            "type": "text",
            "text": {"body": text},
        }

        last_error: Dict[str, Any] = {"error": "unknown"}
        for attempt in range(1, self.settings.retry_attempts + 1):
            try:
                async with httpx.AsyncClient(timeout=self.settings.whatsapp_timeout_seconds) as client:
                    response = await client.post(url, headers=headers, json=payload)
                body = self._json_or_text(response)
                if 200 <= response.status_code < 300:
                    return body
                last_error = {
                    "error": "whatsapp_http_error",
                    "status_code": response.status_code,
                    "body": body,
                    "attempt": attempt,
                }
                logger.warning("WhatsApp send failed: %s", last_error)
            except Exception as exc:  # noqa: BLE001
                last_error = {"error": "whatsapp_request_exception", "details": str(exc), "attempt": attempt}
                logger.warning("WhatsApp request exception: %s", last_error)

            if attempt < self.settings.retry_attempts:
                await asyncio.sleep(self.settings.retry_backoff_seconds * attempt)

        return last_error

    @staticmethod
    def _json_or_text(response: httpx.Response) -> Dict[str, Any]:
        try:
            data = response.json()
            if isinstance(data, dict):
                return data
            return {"data": data}
        except Exception:  # noqa: BLE001
            return {"text": response.text[:500]}

