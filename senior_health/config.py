from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    verify_token: str
    access_token: str
    phone_number_id: str
    graph_api_version: str
    admin_phone: str
    users_csv_path: str
    reminders_csv_path: str
    processed_csv_path: str
    scheduler_poll_seconds: int
    whatsapp_timeout_seconds: int
    retry_attempts: int
    retry_backoff_seconds: float
    health_check_hour_24: int


def _to_int(env_name: str, default: int) -> int:
    value = os.getenv(env_name, str(default))
    try:
        return int(value)
    except ValueError:
        return default


def _to_float(env_name: str, default: float) -> float:
    value = os.getenv(env_name, str(default))
    try:
        return float(value)
    except ValueError:
        return default


def get_settings() -> Settings:
    return Settings(
        verify_token=os.getenv("VERIFY_TOKEN", "swar_health_bot_123"),
        access_token=os.getenv("ACCESS_TOKEN", ""),
        phone_number_id=os.getenv("PHONE_NUMBER_ID", ""),
        graph_api_version=os.getenv("GRAPH_API_VERSION", "v18.0"),
        admin_phone=os.getenv("ADMIN_PHONE", ""),
        users_csv_path=os.getenv("USERS_CSV_PATH", "users.csv"),
        reminders_csv_path=os.getenv("REMINDERS_CSV_PATH", "reminder_logs.csv"),
        processed_csv_path=os.getenv("PROCESSED_CSV_PATH", "processed_messages.csv"),
        scheduler_poll_seconds=_to_int("SCHEDULER_POLL_SECONDS", 20),
        whatsapp_timeout_seconds=_to_int("WHATSAPP_TIMEOUT_SECONDS", 12),
        retry_attempts=_to_int("WHATSAPP_RETRY_ATTEMPTS", 3),
        retry_backoff_seconds=_to_float("WHATSAPP_RETRY_BACKOFF_SECONDS", 1.0),
        health_check_hour_24=_to_int("HEALTH_CHECK_HOUR_24", 9),
    )

