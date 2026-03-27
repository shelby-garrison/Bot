from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import Any, Dict, Set

from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, PlainTextResponse

from senior_health.bot_service import BotService
from senior_health.config import get_settings
from senior_health.logging_config import setup_logging
from senior_health.scheduler_service import SchedulerService
from senior_health.storage import CSVRepository
from senior_health.webhook_parser import parse_incoming_messages
from senior_health.whatsapp_client import WhatsAppClient

load_dotenv()
setup_logging()
logger = logging.getLogger(__name__)

settings = get_settings()
repo = CSVRepository(settings.users_csv_path, settings.reminders_csv_path, settings.processed_csv_path)
whatsapp = WhatsAppClient(settings)
pending_reminders: Set[str] = set()
processed_ids = repo.load_processed_ids()
bot = BotService(settings, repo, whatsapp, pending_reminders, processed_ids)
scheduler = SchedulerService(settings, repo, whatsapp, pending_reminders)


@asynccontextmanager
async def lifespan(_: FastAPI):
    scheduler.start()
    try:
        yield
    finally:
        scheduler.shutdown()


app = FastAPI(lifespan=lifespan)


@app.get("/health")
async def health() -> Dict[str, str]:
    return {"status": "ok"}


@app.api_route("/webhook", methods=["GET", "POST"])
async def webhook(request: Request):
    if request.method == "GET":
        mode = request.query_params.get("hub.mode")
        token = request.query_params.get("hub.verify_token")
        challenge = request.query_params.get("hub.challenge")

        if mode == "subscribe" and token == settings.verify_token:
            return PlainTextResponse(content=challenge or "", status_code=200)
        return PlainTextResponse(content="error", status_code=403)

    try:
        payload: Dict[str, Any] = await request.json()
    except Exception:  # noqa: BLE001
        return JSONResponse({"status": "bad_request"}, status_code=400)

    try:
        messages = parse_incoming_messages(payload)
        if not messages:
            return JSONResponse({"status": "no_message"})
        result = await bot.handle_messages(messages)
        return JSONResponse({"status": "ok", **result})
    except Exception as exc:  # noqa: BLE001
        logger.exception("Webhook handling failed")
        return JSONResponse({"status": "error", "details": str(exc)}, status_code=200)
