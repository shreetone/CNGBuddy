# ===== Django Core =====
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import UserProfile
from .mongo_db import (
    pumps_collection,
    bookings_collection,
    contact_collection,
    support_collection,
    feedback_collection
    
)
from .mongo_db import pumps_collection, feedback_collection
from .utils import get_reminder_time
from .notifications import send_whatsapp, send_email
from datetime import datetime, timedelta
from django.utils import timezone
from django.shortcuts import render
import uuid
import os
import re
import base64
from io import BytesIO
from bson import ObjectId
import qrcode
invoice_id = str(uuid.uuid4())[:8]

def login_redirect(request):
    if request.user.is_staff:
        return redirect("admin_pumps")
    return redirect("dashboard")


def register_user(request):
    form = UserCreationForm(request.POST or None)

    for field in form.fields.values():
        field.widget.attrs.update({
            "class": "form-control form-control-lg"
        })

    if request.method == "POST" and form.is_valid():
        user = form.save(commit=False)
        user.email = request.POST.get("email")
        user.save()
        UserProfile.objects.create(
            user=user,
            phone=request.POST.get("phone")
        )
        return redirect("login")

    return render(request, "register.html", {"form": form})

def home(request):
    query = request.GET.get("q", "").strip()

    # 🔍 SEARCH LOGIC
    if query:
        pumps = list(
            pumps_collection.find({
                "is_active": True,
                "$or": [
                    {"name": {"$regex": query, "$options": "i"}},
                    {"address": {"$regex": query, "$options": "i"}}
                ]
            })
        )
    else:
        pumps = list(pumps_collection.find({"is_active": True}))

    # 🔑 Mongo _id → string
    for p in pumps:
        p["mongo_id"] = str(p["_id"])

        # 🔥 image fallback
        if not p.get("image"):
            p["image"] = "/static/default_pump.jpg"

    return render(request, "home.html", {
        "pumps": pumps,
        "search_query": query
    })
def admin_login(request):
    error = None

    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)

        if user and user.is_staff:
            login(request, user)
            return redirect("admin_pumps")
        else:
            error = "Invalid admin credentials"

    return render(request, "admin_login.html", {"error": error})

def register_user(request):
    form = UserCreationForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        user = form.save(commit=False)
        user.email = request.POST.get("email")
        user.save()
        support_collection.insert_one({
            "type": "profile",
            "username": user.username,
            "email": user.email,
            "phone": request.POST.get("phone"),
            "created_at": datetime.utcnow()
        })

        return redirect("login")

    return render(request, "register.html", {"form": form})

@login_required
def dashboard(request):
    bookings = list(bookings_collection.find({"user": request.user.username}))

    for b in bookings:
        b["id"] = str(b["_id"]) 

    return render(request, "dashboard.html", {"bookings": bookings})

def pump_detail(request, pump_id):
    pump = pumps_collection.find_one({"_id": ObjectId(pump_id)})
    if not pump:
        return redirect("home")

    pump["mongo_id"] = str(pump["_id"])
    return render(request, "pump_detail.html", {"pump": pump})

def pump_queue(request, pump_id):
    pump = pumps_collection.find_one({"_id": ObjectId(pump_id)})
    if not pump:
        return JsonResponse({"error": "Pump not found"}, status=404)

    return JsonResponse({
        "queue": pump.get("queue", 0),
        "avg_service_time": pump.get("avg_service_time", 5)
    })

@login_required
def book_pump(request, pump_id):
    pump = pumps_collection.find_one({"_id": ObjectId(pump_id)})
    if not pump:
        return redirect("home")

    pump["mongo_id"] = str(pump["_id"])

    slots = []
    start = datetime.strptime("00:00", "%H:%M")
    end = datetime.strptime("23:45", "%H:%M")

    while start <= end:
        nxt = start + timedelta(minutes=15)
        slots.append(f"{start.strftime('%H:%M')} - {nxt.strftime('%H:%M')}")
        start = nxt

    if request.method == "POST":
        profile, _ = UserProfile.objects.get_or_create(
            user=request.user,
            defaults={"phone": "0000000000"}
        )

        booking_id = str(uuid.uuid4())[:8]

        bookings_collection.insert_one({
            "booking_id": booking_id,
            "user": request.user.username,
            "email": request.user.email,
            "phone": profile.phone,  
            "pump_id": pump_id,
            "pump_name": pump["name"],
            "date": request.POST["date"],
            "time_slot": request.POST["time_slot"],
            "vehicle_type": request.POST["vehicle_type"],
            "vehicle_number": request.POST["vehicle_number"],
            "amount": 20,
            "status": "pending_payment",
            "created_at": datetime.utcnow()
        })

        pumps_collection.update_one(
            {"_id": ObjectId(pump_id)},
            {"$inc": {"queue": 1}}
        )

        return redirect("dashboard")

    return render(request, "book_pump.html", {
        "pump": pump,
        "slots": slots,
        "today": datetime.today().date()
    })

    return render(request, "book_pump.html", {
        "pump": pump,
        "slots": slots,
        "today": datetime.today().date()
    })

@staff_member_required
def admin_pumps(request):
    pumps = list(pumps_collection.find())
    for p in pumps:
        p["id"] = str(p["_id"])
    return render(request, "admin_pumps.html", {"pumps": pumps})

@staff_member_required
def admin_add_pump(request):
    if request.method == "POST":
        name = request.POST.get("name")
        address = request.POST.get("address")
        lat = float(request.POST.get("lat"))
        lng = float(request.POST.get("lng"))

        image = request.POST.get("image")
        if not image:
            image = "default_pump.jpg"

        pumps_collection.insert_one({
            "name": name,
            "address": address,
            "lat": lat,
            "lng": lng,
            "queue": 0,
            "image": image,
            "is_active": True,
        })

        return redirect("admin_pumps")  
    return render(request, "add_pump.html")

@staff_member_required
def admin_delete_pump(request, pump_id):
    pumps_collection.delete_one({"_id": ObjectId(pump_id)})
    return redirect("admin_pumps")

@staff_member_required
def admin_edit_pump(request, pump_id):
    pump = pumps_collection.find_one({"_id": ObjectId(pump_id)})
    if not pump:
        return redirect("admin_pumps")

    if request.method == "POST":
        pumps_collection.update_one(
            {"_id": ObjectId(pump_id)},
            {"$set": {
                "name": request.POST["name"],
                "address": request.POST["address"],
                "lat": float(request.POST["lat"]),
                "lng": float(request.POST["lng"]),
                "avg_service_time": int(request.POST["avg_service_time"]),
            }}
        )
        return redirect("admin_pumps")

    pump["id"] = str(pump["_id"])
    return render(request, "edit_pump.html", {"pump": pump})

@staff_member_required
def toggle_pump(request, pump_id):
    pump = pumps_collection.find_one({"_id": ObjectId(pump_id)})

    if pump:
        pumps_collection.update_one(
            {"_id": ObjectId(pump_id)},
            {"$set": {"is_active": not pump.get("is_active", True)}}
        )

    return redirect("admin_pumps")

@staff_member_required
def admin_analytics(request):
    total_pumps = pumps_collection.count_documents({})
    active_pumps = pumps_collection.count_documents({"is_active": True})
    total_bookings = bookings_collection.count_documents({})
    paid_bookings = bookings_collection.count_documents({"status": "paid"})

    revenue = sum(
        b["amount"] for b in bookings_collection.find({"status": "paid"})
    )

    return render(request, "admin_analytics.html", {
        "total_pumps": total_pumps,
        "active_pumps": active_pumps,
        "total_bookings": total_bookings,
        "paid_bookings": paid_bookings,
        "revenue": revenue
    })

def map_view(request):
    pumps = list(pumps_collection.find({"is_active": True}))

    for p in pumps:
        p["id"] = str(p["_id"])

    return render(request, "map.html", {
        "pumps": pumps,
        "google_key": settings.GOOGLE_MAPS_API_KEY
    })

def nearest_pumps(request):
    lat = float(request.GET.get("lat"))
    lng = float(request.GET.get("lng"))

    pumps = list(pumps_collection.find({"is_active": True}))
    for p in pumps:
        p["id"] = str(p["_id"])
        p["address"] = p.get("address", "")
        p["queue"] = p.get("queue", 0)
        p["distance"] = abs(p["lat"] - lat) + abs(p["lng"] - lng)

    pumps.sort(key=lambda x: x["distance"])
    return JsonResponse({"pumps": pumps[:5]})

@login_required
def support_ticket(request):
    if request.method == "POST":
        support_collection.insert_one({
            "user": request.user.username,
            "message": request.POST["message"],
            "created_at": datetime.utcnow()
        })
        return redirect("dashboard")

    return render(request, "support.html")

@staff_member_required
def admin_support(request):
    tickets = list(support_collection.find().sort("created_at", -1))
    for t in tickets:
        t["id"] = str(t["_id"])
    return render(request, "admin_support.html", {
        "tickets": tickets
    })

@staff_member_required
def delete_ticket(request, ticket_id):
    support_collection.delete_one(
        {"_id": ObjectId(ticket_id)}
    )
    return redirect("admin_support")

@staff_member_required
def admin_contacts(request):
    contacts = list(contact_collection.find().sort("created_at", -1))
    for c in contacts:
        c["id"] = str(c["_id"])

    return render(request, "admin_contacts.html", {
        "contacts": contacts
    })

@login_required
def payment_history(request):
    payments = list(bookings_collection.find({
        "user": request.user.username,
        "status": "paid"
    }).sort("created_at", -1))

    return render(request, "payment_history.html", {"payments": payments})

@login_required
def profile(request):
    total = bookings_collection.count_documents({
        "user": request.user.username
    })

    return render(request, "profile.html", {
        "total_bookings": total
    })

def contact_view(request):
    if request.method == "POST":
        contact_collection.insert_one({
            "name": request.POST["name"],
            "email": request.POST["email"],
            "message": request.POST["message"],
            "created_at": datetime.utcnow()
        })
        messages.success(request, "Message sent successfully")

    return render(request, "contact.html")

def about(request):
    faqs = [
        {
            "question": "What is CNG Buddy?",
            "answer": "CNG Buddy is a smart platform that helps users find nearby CNG pumps, check live queues, and book time slots in advance."
        },
        {
            "question": "Who can use CNG Buddy?",
            "answer": "Anyone using CNG vehicles including auto drivers, cab drivers, and private vehicle owners."
        },
        {
            "question": "Is booking mandatory?",
            "answer": "No, but booking helps save time and avoid long queues."
        },
        {
            "question": "How accurate is live queue data?",
            "answer": "Queue data is updated in real time by the pump system and bookings."
        },
        {
            "question": "Is CNG Buddy free?",
            "answer": "Yes, basic features are free for users."
        }
    ]

    return render(request, "about.html", {"faqs": faqs})

def create_user_profile(user, phone):
    from .mongo_db import support_collection
    support_collection.insert_one({
        "type": "profile",
        "username": user.username,
        "email": user.email,
        "phone": phone,
        "created_at": datetime.utcnow()
    })

@login_required
def cancel_booking(request, booking_id):
    booking = bookings_collection.find_one({"booking_id": booking_id})

    if not booking:
        return redirect("dashboard")

    if booking["user"] != request.user.username and not request.user.is_staff:
        return redirect("dashboard")

    if booking["status"] != "paid":
        return redirect("dashboard")

    pumps_collection.update_one(
        {"_id": ObjectId(booking["pump_id"])},
        {"$inc": {"queue": -1}}
    )
    bookings_collection.update_one(
        {"booking_id": booking_id},
        {"$set": {"status": "cancelled"}}
    )

    return redirect("dashboard")

@login_required
def reschedule_booking(request, booking_id):

    booking = bookings_collection.find_one({
        "booking_id": booking_id,
        "user": request.user.username
    })

    if not booking:
        return redirect("dashboard")

    pump = pumps_collection.find_one({"_id": ObjectId(booking["pump_id"])})
    slots = []
    start = datetime.strptime("00:00", "%H:%M")
    end = datetime.strptime("23:45", "%H:%M")

    while start <= end:
        next_time = start + timedelta(minutes=15)
        slots.append(f"{start.strftime('%H:%M')} - {next_time.strftime('%H:%M')}")
        start = next_time

    if request.method == "POST":
        new_date = request.POST["date"]
        new_slot = request.POST["time_slot"]
        bookings_collection.update_one(
            {"booking_id": booking_id},
            {
                "$set": {
                    "date": new_date,
                    "time_slot": new_slot,
                    "rescheduled_at": datetime.utcnow()
                }
            }
        )
        return redirect("dashboard")

    return render(request, "reschedule_booking.html", {
        "booking": booking,
        "pump": pump,
        "slots": slots,
        "today": datetime.today().date()
    })

@login_required
def profile_view(request):
    profile, _ = UserProfile.objects.get_or_create(user=request.user)

    if request.method == "POST":
        profile.whatsapp_alert = "whatsapp_alert" in request.POST
        profile.email_alert = "email_alert" in request.POST
        profile.save()

    return render(request, "profile.html", {"profile": profile})

@staff_member_required
def admin_bookings(request):
    bookings = list(bookings_collection.find().sort("created_at", -1))

    for b in bookings:
        b["id"] = str(b["_id"])
        b["user"] = b.get("user", "")
        b["email"] = b.get("email", "")
        b["phone"] = b.get("phone", "")
        b["pump_name"] = b.get("pump_name", "")
        b["date"] = b.get("date", "")
        b["time_slot"] = b.get("time_slot", "")
        b["vehicle_number"] = b.get("vehicle_number", "")
        b["amount"] = b.get("amount", 0)
        b["status"] = b.get("status", "unknown")

    return render(request, "admin_bookings.html", {
        "bookings": bookings
    })

@login_required
def payment(request, booking_id):
    booking = bookings_collection.find_one({"booking_id": booking_id})
    if not booking:
        return redirect("dashboard")

    if request.method == "POST":
        bookings_collection.update_one(
            {"booking_id": booking_id},
            {"$set": {
                "status": "paid",
                "payment_method": "Cash on Delivery",
                "paid_at": datetime.utcnow()
            }}
        )
        return redirect("invoice", booking_id=booking_id)

    return render(request, "payment.html", {
        "booking": booking
    })

def generate_qr(data):
    qr = qrcode.make(data)
    buffer = BytesIO()
    qr.save(buffer, format="PNG")
    return base64.b64encode(buffer.getvalue()).decode()

@login_required
def invoice(request, booking_id):
    booking = bookings_collection.find_one({"booking_id": booking_id})

    if not booking:
        return redirect("dashboard")

    booking["id"] = booking["booking_id"]
    qr_code = generate_qr(booking_id)

    return render(request, "invoice.html", {
        "booking": booking,
        "qr_code": qr_code
    })

@login_required
def dashboard(request):
    bookings = list(bookings_collection.find({"user": request.user.username}))

    for b in bookings:
        b["id"] = b.get("booking_id")   # 🔥 THIS IS THE FIX

    return render(request, "dashboard.html", {
        "bookings": bookings
    })

def terms(request):
    return render(request, "terms.html")

def privacy(request):
    return render(request, "privacy.html")

def contact_view(request):
    if request.method == "POST":
        contact_collection.insert_one({
            "name": request.POST["name"],
            "email": request.POST["email"],
            "message": request.POST["message"],
            "created_at": datetime.utcnow()
        })
        messages.success(request, "Message sent successfully")

    return render(request, "contacts.html")

@staff_member_required
def contacts(request):
    contacts = list(contact_collection.find().sort("created_at", -1))
    for c in contacts:
        c["id"] = str(c["_id"])
    return render(request, "contacts.html", {
        "contacts": contacts
    })

def support(request):
    return render(request, "support.html")

def login_redirect(request):
    if request.user.is_staff:
        return redirect("admin_pumps")
    return redirect("dashboard")

def search_suggestions(request):
    q = request.GET.get("q", "").strip()

    results = []
    if q:
        cursor = pumps_collection.find(
            {
                "$or": [
                    {"name": {"$regex": q, "$options": "i"}},
                    {"address": {"$regex": q, "$options": "i"}}
                ]
            },
            {"name": 1, "address": 1}
        ).limit(5)

        for p in cursor:
            results.append({
                "name": p.get("name"),
                "address": p.get("address")
            })

    return JsonResponse({"results": results})

@login_required
def test_reminder(request):
    profile = request.user.userprofile

    send_whatsapp(
        profile.phone,
        "Reminder: Your CNG slot is in 30 minutes."
    )

    send_email_notification(
        request.user.email,
        "CNG Buddy Reminder",
        "Your CNG slot is in 30 minutes."
    )

    return redirect("dashboard")

@login_required
def test_reminder(request):
    profile = request.user.userprofile

    send_whatsapp(
        profile.phone,
        "Reminder: Your CNG slot is in 30 minutes."
    )

    send_email_notification(
        request.user.email,
        "CNG Buddy Reminder",
        "Your CNG slot is in 30 minutes."
    )

    return redirect("dashboard")

@staff_member_required
def admin_bookings(request):
    status = request.GET.get("status")
    pump = request.GET.get("pump")

    query = {}

    if status:
        query["status"] = status

    if pump:
        query["pump_name"] = {"$regex": pump, "$options": "i"}

    bookings = list(bookings_collection.find(query).sort("created_at", -1))

    return render(request, "admin_bookings.html", {
        "bookings": bookings
    })

def send_slot_reminders():
    now = datetime.utcnow()

    bookings = bookings_collection.find({"status": "paid"})

    for b in bookings:
        reminder_time = get_reminder_time(b["date"], b["time_slot"])

        if abs((now - reminder_time).total_seconds()) < 60:
            user = User.objects.get(username=b["user"])
            profile = user.userprofile

            message = (
                f"CNG Buddy Reminder\n\n"
                f"Pump: {b['pump_name']}\n"
                f"Time: {b['time_slot']}\n"
                f"Vehicle: {b['vehicle_number']}\n\n"
                f"Please reach on time."
            )

            if profile.whatsapp_alert:
                send_whatsapp(profile.phone, message)

            if profile.email_alert:
                send_email(
                    user.email,
                    "CNG Slot Reminder",
                    message
                )

@login_required
def rate_pump(request, pump_id):
    if request.method == "POST":
        rating = int(request.POST.get("rating"))
        pump = pumps_collection.find_one(
            {"_id": ObjectId(pump_id)}
        )

        if not pump:
            return redirect("home") 
        total = pump.get("rating", 0) * pump.get("rating_count", 0)
        total += rating

        new_count = pump.get("rating_count", 0) + 1
        new_rating = round(total / new_count, 1)

        pumps_collection.update_one(
            {"_id": ObjectId(pump_id)},
            {"$set": {
                "rating": new_rating,
                "rating_count": new_count
            }}
        )

    return redirect("pump_detail", pump_id=pump_id)

@login_required
def submit_feedback(request):
    if request.method == "POST":
        rating = int(request.POST.get("rating"))
        comment = request.POST.get("comment")

        feedback_collection.insert_one({
    "username": request.user.username,
    "comment": request.POST.get("comment"),
    "rating": int(request.POST.get("rating")),
    "created_at": datetime.utcnow(),
    "is_approved": False 
})


        return redirect("home")

    # ✅ GET → SHOW FEEDBACK FORM
    return render(request, "feedback.html")

def home(request):
    query = request.GET.get("q", "").strip()

    if query:
        pumps = list(pumps_collection.find({
            "$or": [
                {"name": {"$regex": query, "$options": "i"}},
                {"address": {"$regex": query, "$options": "i"}}
            ],
            "is_active": True
        }))
    else:
        pumps = list(pumps_collection.find({"is_active": True}))

    for p in pumps:
        p["mongo_id"] = str(p["_id"])

    

    feedbacks=list(feedback_collection.find({"is_approved":True}))

    return render(request, "home.html", {
        "pumps": pumps,
        "search": query
    })

@staff_member_required
def admin_feedbacks(request):
    feedbacks = list(feedback_collection.find())
    for f in feedbacks:
        f["id"] = str(f["_id"])
    return render(request, "admin_feedback.html", {
        "feedbacks": feedbacks
    })


@staff_member_required
def approve_feedback(request,feedback_id):
    feedback_collection.update_one(
        {"_id":ObjectId(feedback_id)},
        {"$set":{"is_approved":True}}
    )
    return redirect("admin_feedback")

@staff_member_required
def delete_feedback(request,feedback_id):
    feedback_collection.delete_one(
        {"_id":ObjectId(feedback_id)}
    )
    return redirect("admin_feedback")