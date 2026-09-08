# main/notifications.py

from twilio.rest import Client
from django.conf import settings
from django.core.mail import send_mail


# ✅ WhatsApp sender
def send_whatsapp(phone, message):
    client = Client(
        settings.TWILIO_ACCOUNT_SID,
        settings.TWILIO_AUTH_TOKEN
    )

    client.messages.create(
        from_=settings.TWILIO_WHATSAPP,
        to=f"whatsapp:{phone}",
        body=message
    )


# ✅ Email sender  (🔥 THIS WAS MISSING)
def send_email(email, subject, message):
    send_mail(
        subject,
        message,
        settings.EMAIL_HOST_USER,
        [email],
        fail_silently=True
    )
