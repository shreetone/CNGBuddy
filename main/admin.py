from django.contrib import admin
from django.contrib.auth.models import User
from .models import UserProfile, Booking, Payment

# ---------------- USER PROFILE ----------------
@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "phone", "whatsapp_alert", "email_alert")
    search_fields = ("user__username", "phone", "vehicle_number")


# ---------------- BOOKING ----------------
@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ("user", "pump_name", "datetime", "status")
    list_filter = ("status",)
    search_fields = ("user__username", "pump_name")


# ---------------- PAYMENT ----------------
@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ("booking", "amount", "status", "paid_at")
    list_filter = ("status",)
