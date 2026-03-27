from __future__ import annotations

import asyncio
import logging
from datetime import datetime
from typing import Dict, Iterable, Set

from senior_health.assistant_rules import is_unwell_response, rule_based_reply
from senior_health.config import Settings
from senior_health.models import IncomingMessage, RegistrationState, ReminderLog, UserRecord
from senior_health.state_machine import RegistrationMachine
from senior_health.storage import CSVRepository
from senior_health.whatsapp_client import WhatsAppClient

logger = logging.getLogger(__name__)


class BotService:
    def __init__(
        self,
        settings: Settings,
        repo: CSVRepository,
        whatsapp: WhatsAppClient,
        pending_reminders: Set[str],
        processed_ids: Set[str],
    ) -> None:
        self.settings = settings
        self.repo = repo
        self.whatsapp = whatsapp
        self.pending_reminders = pending_reminders
        self.processed_ids = processed_ids
        self.machine = RegistrationMachine()

    async def handle_messages(self, messages: Iterable[IncomingMessage]) -> Dict[str, int]:
        processed = 0
        ignored = 0
        for msg in messages:
            if self._already_processed(msg.message_id):
                ignored += 1
                continue
            await self._handle_single(msg)
            self._mark_processed(msg.message_id)
            processed += 1
        return {"processed": processed, "ignored": ignored}

    async def _handle_single(self, msg: IncomingMessage) -> None:
        text = msg.text.strip()
        lower = text.lower()
        user = self.repo.get_user(msg.from_phone)
        user = self.machine.start_or_get(user, msg.from_phone)

        # Admin command: stats
        if lower == "stats" and self._is_admin(msg.from_phone):
            await self.whatsapp.send_text(msg.from_phone, self._build_stats_report())
            return

        # Reminder response tracking.
        if user.state == RegistrationState.DONE and lower in {"1", "2"} and msg.from_phone in self.pending_reminders:
            self.pending_reminders.discard(msg.from_phone)
            if lower == "1":
                user.adherence_taken += 1
                self.repo.upsert_user(user)
                self.repo.append_reminder_log(
                    ReminderLog.new(
                        event_id=f"response-{msg.message_id}",
                        phone=user.phone,
                        medicine=user.medicine,
                        reminder_time=user.reminder_time,
                        response="taken",
                        response_delay_minutes="",
                    )
                )
                await self.whatsapp.send_text(user.phone, "Great. Stay healthy.")
            else:
                self.repo.upsert_user(user)
                self.repo.append_reminder_log(
                    ReminderLog.new(
                        event_id=f"response-{msg.message_id}",
                        phone=user.phone,
                        medicine=user.medicine,
                        reminder_time=user.reminder_time,
                        response="not_taken",
                        response_delay_minutes="",
                    )
                )
                if user.caregiver:
                    await self.whatsapp.send_text(
                        user.caregiver,
                        f"Alert: {user.name or user.phone} has not taken medicine yet.",
                    )
                await self.whatsapp.send_text(user.phone, "Caregiver has been notified.")
            return

        # Daily health check reply handling.
        if user.awaiting_health_reply:
            user.awaiting_health_reply = False
            self.repo.upsert_user(user)
            if is_unwell_response(lower):
                if user.caregiver:
                    await self.whatsapp.send_text(
                        user.caregiver,
                        f"Health Alert: {user.name or user.phone} reported feeling unwell.",
                    )
                await self.whatsapp.send_text(user.phone, "Thanks for sharing. Caregiver has been informed.")
            else:
                await self.whatsapp.send_text(user.phone, "Good to hear. Keep taking your medicines on time.")
            return

        # Registration flow for not-yet-complete users.
        if user.state != RegistrationState.DONE or lower in {"hi", "hello", "start", "register"}:
            result = self.machine.transition(user, text)
            self.repo.upsert_user(result.updated_user)
            await self.whatsapp.send_text(user.phone, result.reply_text)
            return

        # Rule-based assistant fallback.
        assistant_reply = rule_based_reply(text)
        if assistant_reply:
            await self.whatsapp.send_text(user.phone, assistant_reply)
            return

        await self.whatsapp.send_text(
            user.phone,
            "I did not understand that. Reply 1 or 2 after reminders, or type help.",
        )

    def _already_processed(self, message_id: str) -> bool:
        return bool(message_id) and (message_id in self.processed_ids or self.repo.is_processed(message_id))

    def _mark_processed(self, message_id: str) -> None:
        if not message_id:
            return
        self.repo.mark_processed(message_id)
        self.processed_ids.add(message_id)

    def _is_admin(self, phone: str) -> bool:
        normalized = "".join(ch for ch in str(phone) if ch.isdigit())
        admin = "".join(ch for ch in self.settings.admin_phone if ch.isdigit())
        return bool(admin) and normalized == admin

    def _build_stats_report(self) -> str:
        users = self.repo.list_users()
        if not users:
            return "No users registered yet."
        lines = ["Adherence Stats:"]
        for user in users:
            lines.append(
                f"- {user.name or user.phone}: {user.adherence_taken}/{user.adherence_total} "
                f"({user.adherence_pct():.1f}%)"
            )
        return "\n".join(lines)

