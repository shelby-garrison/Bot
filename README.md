# Senior Health Companion (FastAPI + WhatsApp Cloud API)

Production-oriented WhatsApp bot for senior medication workflows:
- Webhook verification + message processing
- Stateful registration flow
- Reminder scheduling + adherence tracking
- Caregiver alerts
- Admin stats
- Rule-based assistant
- Daily health check alerts

## Folder Structure

```text
Senior-Health-Companion-main/
  app.py
  .env.example
  requirements.txt.txt
  users.csv
  reminder_logs.csv
  processed_messages.csv
  senior_health/
    __init__.py
    config.py
    logging_config.py
    models.py
    storage.py
    webhook_parser.py
    state_machine.py
    assistant_rules.py
    whatsapp_client.py
    bot_service.py
    scheduler_service.py
```

## Environment Setup

1) Create `.env` from `.env.example` and update values:
- `ACCESS_TOKEN`
- `PHONE_NUMBER_ID`
- `VERIFY_TOKEN`
- `ADMIN_PHONE`

2) Install dependencies:

```bash
pip install -r requirements.txt.txt
```

3) Run server:

```bash
uvicorn app:app --reload --host 127.0.0.1 --port 8000
```
OR
```bash
 .\.venv\Scripts\python -m uvicorn app:app --reload --host 127.0.0.1 --port 8000
```
## Webhook Setup

- Callback URL: `https://<public-url>/webhook`
- Verify token: value of `VERIFY_TOKEN`

`GET /webhook` validates verification handshake.

`POST /webhook` parses incoming WhatsApp messages and handles:
- Registration transitions
- Reminder responses (`1`, `2`)
- Admin command (`stats`)
- Rule-based assistant fallback
- Daily health check responses

## Core Commands

- `hi` or `register`: start registration
- `1`: medicine taken (when reminder pending)
- `2`: medicine not taken (caregiver alert)
- `stats`: admin-only adherence comparison
- `help`: show supported interactions

## Sample Payload (POST /webhook)

```json
{
  "object": "whatsapp_business_account",
  "entry": [
    {
      "id": "1924442351516706",
      "changes": [
        {
          "value": {
            "messaging_product": "whatsapp",
            "metadata": {
              "display_phone_number": "15551441655",
              "phone_number_id": "954859211055275"
            },
            "contacts": [
              {
                "profile": { "name": "Swar Sharma" },
                "wa_id": "918657120105"
              }
            ],
            "messages": [
              {
                "from": "918657120105",
                "id": "wamid.HBg...",
                "timestamp": "1773927055",
                "text": { "body": "hi" },
                "type": "text"
              }
            ]
          },
          "field": "messages"
        }
      ]
    }
  ]
}
```

## Architecture Notes

- Modular layers:
  - `webhook_parser.py`: payload normalization
  - `state_machine.py`: deterministic registration transitions
  - `storage.py`: CSV abstraction + locking
  - `bot_service.py`: orchestration and business rules
  - `scheduler_service.py`: reminders + daily health checks
  - `whatsapp_client.py`: API calls with retries
- Idempotency:
  - Processed message IDs are persisted (`processed_messages.csv`)
  - Duplicate webhook retries are ignored safely
- Concurrency:
  - CSV operations use a lock for safe multi-request access
- Reliability:
  - Webhook handles malformed payloads and continues safely
  - WhatsApp API retries configured via env vars