from pymongo import MongoClient

client = MongoClient("mongodb://localhost:27017/")
db = client["cng_buddy_db"]

pumps_collection = db["pumps"]
bookings_collection = db["bookings"]
support_collection = db["support"]
users_collection = db["users"]
payments_collection = db["payments"]
analytics_collection = db["analytics"]
contact_collection = db["contact_messages"]
feedback_collection = db["feedback"]

