from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional

from senior_health.models import RegistrationState, UserRecord


@dataclass
class TransitionResult:
    updated_user: UserRecord
    reply_text: str


class RegistrationMachine:
    @staticmethod
    def start_or_get(user: Optional[UserRecord], phone: str) -> UserRecord:
        if user:
            return user
        return UserRecord(phone=phone, state=RegistrationState.LANGUAGE)

    def transition(self, user: UserRecord, incoming_text: str) -> TransitionResult:
        text = incoming_text.strip()
        lower = text.lower()

        if lower in {"hi", "hello", "start", "register"}:
            user.state = RegistrationState.LANGUAGE
            return TransitionResult(
                updated_user=user,
                reply_text="Welcome to Senior Health Companion.\nSelect language:\n1 English\n2 Hindi",
            )

        if user.state == RegistrationState.LANGUAGE:
            if lower not in {"1", "2"}:
                return TransitionResult(user, "Invalid choice. Reply 1 for English or 2 for Hindi.")
            user.language = "English" if lower == "1" else "Hindi"
            user.state = RegistrationState.NAME
            return TransitionResult(user, "Please enter your name.")

        if user.state == RegistrationState.NAME:
            if not text:
                return TransitionResult(user, "Name cannot be empty. Please enter your name.")
            user.name = text
            user.state = RegistrationState.AGE
            return TransitionResult(user, "Enter your age.")

        if user.state == RegistrationState.AGE:
            if not text.isdigit() or not (40 <= int(text) <= 120):
                return TransitionResult(user, "Please enter a valid age between 40 and 120.")
            user.age = text
            user.state = RegistrationState.CAREGIVER
            return TransitionResult(user, "Enter caregiver phone number with country code.")

        if user.state == RegistrationState.CAREGIVER:
            digits = "".join(ch for ch in text if ch.isdigit())
            if not re.fullmatch(r"\d{10,15}", digits):
                return TransitionResult(user, "Invalid phone number. Enter 10-15 digits with country code.")
            user.caregiver = digits
            user.state = RegistrationState.MEDICINE
            return TransitionResult(user, "Enter medicine name.")

        if user.state == RegistrationState.MEDICINE:
            if not text:
                return TransitionResult(user, "Medicine name cannot be empty. Enter medicine name.")
            user.medicine = text
            user.state = RegistrationState.TIME
            return TransitionResult(user, "Enter reminder time in HH:MM (24-hour format).")

        if user.state == RegistrationState.TIME:
            if not re.fullmatch(r"(?:[01]\d|2[0-3]):[0-5]\d", text):
                return TransitionResult(user, "Invalid time format. Example: 08:30")
            user.reminder_time = text
            user.state = RegistrationState.DONE
            return TransitionResult(
                user,
                (
                    "Registration complete.\n"
                    f"Medicine: {user.medicine}\nTime: {user.reminder_time}\n"
                    "When reminder comes reply 1 for taken, 2 for not taken."
                ),
            )

        return TransitionResult(user, "You are already registered. Reply 1 or 2 after reminder, or ask a health question.")

