from fastapi import FastAPI, Request
from fastapi.responses import PlainTextResponse, JSONResponse
import requests
import csv
import os
from reminder import start_scheduler
from shared import pending_reminders

app = FastAPI()
print("APP_LOADED:", __file__)

# Configuration
VERIFY_TOKEN = os.getenv("VERIFY_TOKEN", "swar_health_bot_123")
ACCESS_TOKEN = os.getenv(
    "ACCESS_TOKEN",
    "EAAdPF5RRGGcBQ3br2yJE9XHOVqclX7V9aU66ASONVUvVNaASauNU1ZC1st4nyAhMPVDhHkR1SyZAegqZAMWdQRNa2wwCg9w6edLuuyzJuiN6z0le0bWr1e7vkzMCSUCZA63VFcbe9d4ceWUB7mY2m8v6ZBFuuG8FCVLm8uNZB6j9N1Ji4rZA9NZBPJN9eZAvZC1BwEJiSXQHGxF6AqZBc0nbYGifx4EC6BQB4F0bBvGu6v12ozss3Qs9GLmLHu1l7H02oB4JT3zEKQD4uKxQ2qZA99gocN1L",
)
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID", "954859211055275")

# States
LANGUAGE, NAME, AGE, CAREGIVER, MEDICINE, TIME, DONE = "language", "name", "age", "caregiver", "medicine", "time", "done"

user_states = {}
user_data = {}

# CSV Setup
if not os.path.exists("users.csv"):
    with open("users.csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["phone", "name", "age", "language", "caregiver", "medicine", "time"])

def send_message(to, text):
    # WhatsApp "to" / wA_id must be digits only.
    to = "".join(ch for ch in str(to) if ch.isdigit())

    url = f"https://graph.facebook.com/v18.0/{PHONE_NUMBER_ID}/messages"
    headers = {"Authorization": f"Bearer {ACCESS_TOKEN}", "Content-Type": "application/json"}
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {"body": text}
    }
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=15)
    except requests.RequestException as e:
        # Never crash webhook handler due to network issues.
        return {"error": "send_message_request_failed", "details": str(e)}

    # Graph usually returns JSON errors, but not always. Be defensive.
    try:
        return response.json()
    except ValueError:
        return {"error": "non_json_response", "status_code": response.status_code, "text": response.text[:300]}

def alert_caretaker(caregiver_phone, user_name):
    send_message(caregiver_phone, f"⚠️ Alert: {user_name} may have missed their medicine!")

@app.api_route("/webhook", methods=["GET", "POST"])
async def webhook(request: Request):

    # ---------------------------
    # 1. VERIFICATION (GET)
    # ---------------------------
    if request.method == "GET":
        mode = request.query_params.get("hub.mode")
        token = request.query_params.get("hub.verify_token")
        challenge = request.query_params.get("hub.challenge")

        print("VERIFY HIT:", mode, token, challenge)  # 👈 ADD THIS

        if mode == "subscribe" and token == VERIFY_TOKEN:
            return PlainTextResponse(content=challenge, status_code=200)

        return PlainTextResponse(content="error", status_code=403)

    # ---------------------------
    # 2. MESSAGE HANDLING (POST)
    # ---------------------------
    if request.method == "POST":
        print("WEBHOOK HIT")
        try:
            try:
                data = await request.json()
            except Exception as e:
                print("webhook json parse failed:", repr(e))
                return JSONResponse({"status": "bad_request"})

            print("RAW:", data)

            entries = data.get("entry", []) if isinstance(data, dict) else []
            handled_any = False

            for entry in entries or []:
                if not isinstance(entry, dict):
                    continue
                changes = entry.get("changes", []) or []
                for change in changes:
                    if not isinstance(change, dict):
                        continue
                    value = change.get("value", {}) or {}
                    if not isinstance(value, dict):
                        continue
                    messages = value.get("messages") or []
                    for message in messages or []:
                        if not isinstance(message, dict):
                            continue

                        phone = message.get("from")
                        if not phone:
                            continue

                        text = message.get("text", {}).get("body", "")
                        if not isinstance(text, str):
                            text = str(text)
                        text = text.lower().strip()

                        print("USER SAID:", text)

                        state = user_states.get(phone)

                        if text == "hi" or text == "hello":
                            user_states[phone] = LANGUAGE
                            user_data[phone] = {}
                            send_message(
                                phone,
                                "👋 Welcome to Senior Health Companion\n\n"
                                "Select Language:\n1️⃣ English\n2️⃣ Hindi",
                            )
                        elif state == LANGUAGE:
                            user_data[phone]["language"] = "English" if text == "1" else "Hindi"
                            user_states[phone] = NAME
                            send_message(phone, "Please enter your name")
                        elif state == NAME:
                            user_data[phone]["name"] = text
                            user_states[phone] = AGE
                            send_message(phone, "Enter your age")
                        elif state == AGE:
                            user_data[phone]["age"] = text
                            user_states[phone] = CAREGIVER
                            send_message(phone, "Enter caregiver phone number (with country code)")
                        elif state == CAREGIVER:
                            user_data[phone]["caregiver"] = "".join(ch for ch in text if ch.isdigit())
                            user_states[phone] = MEDICINE
                            send_message(phone, "Enter medicine name")
                        elif state == MEDICINE:
                            user_data[phone]["medicine"] = text
                            user_states[phone] = TIME
                            send_message(phone, "Enter time (HH:MM in 24-hour format)")
                        elif state == TIME:
                            user_data[phone]["time"] = text
                            with open("users.csv", "a", newline="") as f:
                                writer = csv.writer(f)
                                writer.writerow(
                                    [
                                        phone,
                                        user_data[phone]["name"],
                                        user_data[phone]["age"],
                                        user_data[phone]["language"],
                                        user_data[phone]["caregiver"],
                                        user_data[phone]["medicine"],
                                        user_data[phone]["time"],
                                    ]
                                )
                            user_states[phone] = DONE
                            send_message(
                                phone,
                                f"✅ Registered!\n\n"
                                f"Medicine: {user_data[phone]['medicine']}\n"
                                f"Time: {user_data[phone]['time']}",
                            )
                        elif state == DONE:
                            if text == "1":
                                pending_reminders.pop(phone, None)
                                send_message(phone, "✅ Great! Stay healthy")
                            elif text == "2":
                                pending_reminders.pop(phone, None)
                                caregiver = user_data.get(phone, {}).get("caregiver")
                                name = user_data.get(phone, {}).get("name", "The patient")
                                if caregiver:
                                    alert_caretaker(caregiver, name)
                                    send_message(phone, "⚠️ Caregiver has been notified")
                                else:
                                    send_message(phone, "Error: Caregiver info not found.")
                            else:
                                send_message(phone, "Reply:\n1️⃣ Taken\n2️⃣ Not yet")
                        else:
                            send_message(phone, "Send *Hi* to start the registration.")

                        handled_any = True

            if not handled_any:
                return JSONResponse({"status": "no message"})

            return JSONResponse({"status": "ok"})
        except Exception as e:
            # Last-resort: ensure we never throw and get a 500 from the webhook handler.
            print("Unhandled webhook exception:", repr(e))
            return JSONResponse({"status": "ok", "error": str(e)})

# Start the background scheduler
start_scheduler()
