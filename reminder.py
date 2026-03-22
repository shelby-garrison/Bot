import schedule
import time
import threading
import csv
import requests
import os
from shared import pending_reminders
ACCESS_TOKEN = os.getenv(
    "ACCESS_TOKEN",
    "EAAdPF5RRGGcBQ3br2yJE9XHOVqclX7V9aU66ASONVUvVNaASauNU1ZC1st4nyAhMPVDhHkR1SyZAegqZAMWdQRNa2wwCg9w6edLuuyzJuiN6z0le0bWr1e7vkzMCSUCZA63VFcbe9d4ceWUB7mY2m8v6ZBFuuG8FCVLm8uNZB6j9N1Ji4rZA9NZBPJN9eZAvZC1BwEJiSXQHGxF6AqZBc0nbYGifx4EC6BQB4F0bBvGu6v12ozss3Qs9GLmLHu1l7H02oB4JT3zEKQD4uKxQ2qZA99gocN1L",
)
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID", "954859211055275")

def send_message(to, text):
    # WhatsApp "to" / wA_id must be digits only.
    to = "".join(ch for ch in str(to) if ch.isdigit())

    url = f"https://graph.facebook.com/v18.0/{PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "text": {"body": text}
    }
    try:
        requests.post(url, headers=headers, json=payload, timeout=15)
    except requests.RequestException as e:
        print(f"send_message failed: {e}")

def send_reminders():
    with open("users.csv", "r") as f:
        reader = csv.DictReader(f)

        for row in reader:
            phone = row.get("phone")
            medicine = row.get("medicine") or ""
            if not phone:
                continue

            send_message(phone,
                f"💊 Reminder: Take your {medicine}\n\n"
                "Reply:\n1️⃣ Taken\n2️⃣ Not yet"
            )
            pending_reminders[phone] = True
def check_missed():

    with open("users.csv", "r") as f:
        reader = csv.DictReader(f)

        for row in reader:
            phone = row.get("phone")
            if not phone:
                continue

            if phone in pending_reminders:
                name = row.get("name") or ""
                caregiver = row.get("caregiver") or ""

                if caregiver:
                    send_message(caregiver, f"🚨 ALERT: {name} did NOT respond to medicine reminder!")

                # remove after alert
                pending_reminders.pop(phone, None)
def schedule_reminders():
    # Example: runs every minute (for testing)
    schedule.every(1).minutes.do(send_reminders)
    schedule.every(2).minutes.do(check_missed)
    while True:
        schedule.run_pending()
        time.sleep(1)

def start_scheduler():
    thread = threading.Thread(target=schedule_reminders)
    thread.daemon = True
    thread.start()
