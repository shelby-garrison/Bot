from __future__ import annotations

from typing import Any, Dict, List

from senior_health.models import IncomingMessage


def parse_incoming_messages(payload: Dict[str, Any]) -> List[IncomingMessage]:
    parsed: List[IncomingMessage] = []
    if not isinstance(payload, dict):
        return parsed

    for entry in payload.get("entry", []) or []:
        if not isinstance(entry, dict):
            continue
        for change in entry.get("changes", []) or []:
            if not isinstance(change, dict):
                continue
            value = change.get("value", {}) or {}
            if not isinstance(value, dict):
                continue
            messages = value.get("messages", []) or []
            for msg in messages:
                if not isinstance(msg, dict):
                    continue
                from_phone = str(msg.get("from", "")).strip()
                message_id = str(msg.get("id", "")).strip()
                text = msg.get("text", {}).get("body", "")
                if not isinstance(text, str):
                    text = str(text)
                if not from_phone:
                    continue
                parsed.append(
                    IncomingMessage(
                        message_id=message_id,
                        from_phone=from_phone,
                        text=text.strip(),
                        timestamp=str(msg.get("timestamp", "")).strip() or None,
                    )
                )
    return parsed

