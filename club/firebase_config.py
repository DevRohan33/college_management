import firebase_admin
from firebase_admin import credentials, db

from django.conf import settings
cred = credentials.Certificate(settings.FIREBASE_CONFIG["SERVICE_ACCOUNT_KEY"])

if not firebase_admin._apps:
    firebase_admin.initialize_app(cred, {
        "databaseURL": settings.FIREBASE_CONFIG["DATABASE_URL"]
    })
