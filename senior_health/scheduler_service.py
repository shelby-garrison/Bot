from __future__ import annotations

import asyncio
import logging
from datetime import datetime
from typing import Set

from apscheduler.schedulers.background import BackgroundScheduler

from senior_health.config import Settings
from senior_health.models import ReminderLog, today_iso
from senior_health.storage import CSVRepository
from senior_health.whatsapp_client import WhatsAppClient

logger = logging.getLogger(__name__)


class SchedulerService:
    def __init__(
        self,
        settings: Settings,
        repo: CSVRepository,
        whatsapp: WhatsAppClient,
        pending_reminders: Set[str],
    ) -> None:
        self.settings = settings
        self.repo = repo
        self.whatsapp = whatsapp
        self.pending_reminders = pending_reminders
        self.scheduler = BackgroundScheduler()

    def start(self) -> None:
        self.scheduler.add_job(self._tick, "interval", seconds=self.settings.scheduler_poll_seconds, id="tick")
        self.scheduler.start()
        logger.info("Scheduler started with %ss poll interval", self.settings.scheduler_poll_seconds)

    def shutdown(self) -> None:
        if self.scheduler.running:
            self.scheduler.shutdown(wait=False)
            logger.info("Scheduler stopped")

    def _tick(self) -> None:
        now = datetime.now()
        today = today_iso()
        users = self.repo.list_users()
        for user in users:
            # Reminder dispatch exactly at HH:MM (in current server timezone).
            if user.reminder_time == now.strftime("%H:%M") and user.phone not in self.pending_reminders:
                self.pending_reminders.add(user.phone)
                user.adherence_total += 1
                self.repo.upsert_user(user)
                self.repo.append_reminder_log(
                    ReminderLog.new(
                        event_id=f"reminder-{user.phone}-{now.isoformat()}",
                        phone=user.phone,
                        medicine=user.medicine,
                        reminder_time=user.reminder_time,
                        response="pending",
                    )
                )
                asyncio.run(
                    self.whatsapp.send_text(
                        user.phone,
                        f"Reminder: Take your {user.medicine}.\nReply 1 for Taken, 2 for Not yet.",
                    )
                )

            # Daily health check once per day at configured hour.
            if now.hour == self.settings.health_check_hour_24 and user.last_health_check_date != today:
                user.awaiting_health_reply = True
                user.last_health_check_date = today
                self.repo.upsert_user(user)
                asyncio.run(self.whatsapp.send_text(user.phone, "Daily check: How are you feeling today?"))

