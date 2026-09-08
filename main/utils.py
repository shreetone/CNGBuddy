from datetime import datetime, timedelta
from django.conf import settings
from twilio.rest import Client
from main.mongo_db import bookings_collection


def send_whatsapp_reminders():
    now = datetime.utcnow()
    reminder_time = now + timedelta(minutes=30)

    bookings = bookings_collection.find({
        "status": "paid",
        "reminder_sent": False,
        "slot_datetime": {
            "$lte": reminder_time,
            "$gte": now
        }
    })

    client = Client(
        settings.TWILIO_ACCOUNT_SID,
        settings.TWILIO_AUTH_TOKEN
    )

    for b in bookings:
        message = (
            f"⛽ CNG Buddy Reminder\n\n"
            f"Your booking at {b['pump_name']} is in 30 minutes.\n"
            f"Time Slot: {b['time_slot']}\n\n"
            f"Please arrive on time."
        )

        client.messages.create(
            from_=settings.TWILIO_WHATSAPP,
            to=f"whatsapp:+91{b['phone']}",
            body=message
        )

        bookings_collection.update_one(
            {"_id": b["_id"]},
            {"$set": {"reminder_sent": True}}
        )

from datetime import datetime, timedelta

def get_reminder_time(date, time_slot):
    start_time = time_slot.split("-")[0].strip()   # "10:00"
    slot_datetime = datetime.strptime(
        f"{date} {start_time}",
        "%Y-%m-%d %H:%M"
    )
    return slot_datetime - timedelta(minutes=30)
