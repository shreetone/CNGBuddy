from django.apps import AppConfig
from .mongo_db import pumps_collection

class MainConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'main'

    def ready(self):
        if pumps_collection.count_documents({}) == 0:
            pumps_collection.insert_many([
                {"name": "Green CNG Pump", "location": "Sector 10", "is_open": True},
                {"name": "Eco Fuel Station", "location": "Ring Road", "is_open": True},
                {"name": "City Gas", "location": "Bus Stand", "is_open": False},
            ])

class MainConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'main'

    def ready(self):
        import main.signals