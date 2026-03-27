from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from enum import Enum
from typing import Optional


class RegistrationState(str, Enum):
    LANGUAGE = "language"
    NAME = "name"
    AGE = "age"
    CAREGIVER = "caregiver"
    MEDICINE = "medicine"
    TIME = "time"
    DONE = "done"


@dataclass
class UserRecord:
    phone: str
    language: str = ""
    name: str = ""
    age: str = ""
    caregiver: str = ""
    medicine: str = ""
    reminder_time: str = ""
    state: RegistrationState = RegistrationState.LANGUAGE
    adherence_taken: int = 0
    adherence_total: int = 0
    awaiting_health_reply: bool = False
    last_health_check_date: str = ""
    updated_at: str = ""

    def adherence_pct(self) -> float:
        if self.adherence_total <= 0:
            return 0.0
        return (self.adherence_taken / self.adherence_total) * 100


@dataclass
class IncomingMessage:
    message_id: str
    from_phone: str
    text: str
    timestamp: Optional[str] = None


@dataclass
class ReminderLog:
    event_id: str
    phone: str
    medicine: str
    reminder_time: str
    response: str
    response_delay_minutes: str
    date_iso: str

    @staticmethod
    def new(
        event_id: str,
        phone: str,
        medicine: str,
        reminder_time: str,
        response: str,
        response_delay_minutes: str = "",
    ) -> "ReminderLog":
        return ReminderLog(
            event_id=event_id,
            phone=phone,
            medicine=medicine,
            reminder_time=reminder_time,
            response=response,
            response_delay_minutes=response_delay_minutes,
            date_iso=datetime.utcnow().date().isoformat(),
        )


def today_iso() -> str:
    return date.today().isoformat()

