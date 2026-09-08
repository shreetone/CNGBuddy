from django.db import models
from django.contrib.auth.models import User


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone = models.CharField(max_length=15)

    whatsapp_alert = models.BooleanField(default=True)
    email_alert = models.BooleanField(default=True)

    def __str__(self):
        return self.user.username


class Booking(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    # 🔥 Mongo Pump reference (NO ForeignKey)
    pump_id = models.CharField(max_length=50)      # Mongo _id
    pump_name = models.CharField(max_length=200)   # Display purpose

    datetime = models.DateTimeField()
    status = models.CharField(max_length=50, default="Booked")

    def __str__(self):
        return f"{self.user.username} → {self.pump_name}"


class Payment(models.Model):
    booking = models.OneToOneField(Booking, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    paid_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=50, default="Success")

    def __str__(self):
        return f"{self.booking} - ₹{self.amount}"
