from __future__ import annotations

import csv
import os
import threading
from datetime import datetime
from typing import Dict, Iterable, List, Optional, Set

from senior_health.models import RegistrationState, ReminderLog, UserRecord

USERS_HEADERS = [
    "phone",
    "language",
    "name",
    "age",
    "caregiver",
    "medicine",
    "reminder_time",
    "state",
    "adherence_taken",
    "adherence_total",
    "awaiting_health_reply",
    "last_health_check_date",
    "updated_at",
]

REMINDER_HEADERS = [
    "event_id",
    "phone",
    "medicine",
    "reminder_time",
    "response",
    "response_delay_minutes",
    "date_iso",
]

PROCESSED_HEADERS = ["message_id", "processed_at"]


class CSVRepository:
    def __init__(self, users_csv: str, reminders_csv: str, processed_csv: str) -> None:
        self.users_csv = users_csv
        self.reminders_csv = reminders_csv
        self.processed_csv = processed_csv
        self.lock = threading.Lock()
        self._ensure_files()

    def _ensure_files(self) -> None:
        self._ensure_file(self.users_csv, USERS_HEADERS)
        self._ensure_file(self.reminders_csv, REMINDER_HEADERS)
        self._ensure_file(self.processed_csv, PROCESSED_HEADERS)

    @staticmethod
    def _ensure_file(path: str, headers: List[str]) -> None:
        if os.path.exists(path):
            return
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(headers)

    def _read_user_rows(self) -> List[Dict[str, str]]:
        with open(self.users_csv, "r", newline="", encoding="utf-8") as f:
            return list(csv.DictReader(f))

    def _write_user_rows(self, rows: Iterable[Dict[str, str]]) -> None:
        with open(self.users_csv, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=USERS_HEADERS)
            writer.writeheader()
            writer.writerows(rows)

    def get_user(self, phone: str) -> Optional[UserRecord]:
        with self.lock:
            for row in self._read_user_rows():
                if row.get("phone") == phone:
                    return self._row_to_user(row)
        return None

    def upsert_user(self, user: UserRecord) -> None:
        user.updated_at = datetime.utcnow().isoformat()
        with self.lock:
            rows = self._read_user_rows()
            replaced = False
            for idx, row in enumerate(rows):
                if row.get("phone") == user.phone:
                    rows[idx] = self._user_to_row(user)
                    replaced = True
                    break
            if not replaced:
                rows.append(self._user_to_row(user))
            self._write_user_rows(rows)

    def list_users(self) -> List[UserRecord]:
        with self.lock:
            return [self._row_to_user(row) for row in self._read_user_rows() if row.get("phone")]

    def append_reminder_log(self, log: ReminderLog) -> None:
        with self.lock:
            with open(self.reminders_csv, "a", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=REMINDER_HEADERS)
                writer.writerow(
                    {
                        "event_id": log.event_id,
                        "phone": log.phone,
                        "medicine": log.medicine,
                        "reminder_time": log.reminder_time,
                        "response": log.response,
                        "response_delay_minutes": log.response_delay_minutes,
                        "date_iso": log.date_iso,
                    }
                )

    def mark_processed(self, message_id: str) -> None:
        with self.lock:
            with open(self.processed_csv, "a", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=PROCESSED_HEADERS)
                writer.writerow(
                    {"message_id": message_id, "processed_at": datetime.utcnow().isoformat()}
                )

    def is_processed(self, message_id: str) -> bool:
        if not message_id:
            return False
        with self.lock:
            with open(self.processed_csv, "r", newline="", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row.get("message_id") == message_id:
                        return True
        return False

    def load_processed_ids(self, max_ids: int = 5000) -> Set[str]:
        with self.lock:
            with open(self.processed_csv, "r", newline="", encoding="utf-8") as f:
                rows = list(csv.DictReader(f))
        trimmed = rows[-max_ids:]
        return {row["message_id"] for row in trimmed if row.get("message_id")}

    @staticmethod
    def _row_to_user(row: Dict[str, str]) -> UserRecord:
        state = row.get("state", RegistrationState.LANGUAGE.value)
        try:
            parsed_state = RegistrationState(state)
        except ValueError:
            parsed_state = RegistrationState.LANGUAGE
        return UserRecord(
            phone=row.get("phone", ""),
            language=row.get("language", ""),
            name=row.get("name", ""),
            age=row.get("age", ""),
            caregiver=row.get("caregiver", ""),
            medicine=row.get("medicine", ""),
            reminder_time=row.get("reminder_time", ""),
            state=parsed_state,
            adherence_taken=int(row.get("adherence_taken", "0") or 0),
            adherence_total=int(row.get("adherence_total", "0") or 0),
            awaiting_health_reply=(row.get("awaiting_health_reply", "false").lower() == "true"),
            last_health_check_date=row.get("last_health_check_date", ""),
            updated_at=row.get("updated_at", ""),
        )

    @staticmethod
    def _user_to_row(user: UserRecord) -> Dict[str, str]:
        return {
            "phone": user.phone,
            "language": user.language,
            "name": user.name,
            "age": user.age,
            "caregiver": user.caregiver,
            "medicine": user.medicine,
            "reminder_time": user.reminder_time,
            "state": user.state.value,
            "adherence_taken": str(user.adherence_taken),
            "adherence_total": str(user.adherence_total),
            "awaiting_health_reply": str(user.awaiting_health_reply).lower(),
            "last_health_check_date": user.last_health_check_date,
            "updated_at": user.updated_at,
        }

