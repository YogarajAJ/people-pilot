import os
import firebase_admin
from firebase_admin import credentials, firestore

# Get credentials path from an environment variable (default to /serviceAccountKey.json)
FIREBASE_CREDENTIALS_PATH = os.getenv("FIREBASE_CREDENTIALS", "/serviceAccountKey.json")

# Check if the credentials file exists
if not os.path.exists(FIREBASE_CREDENTIALS_PATH):
    raise FileNotFoundError(f"Firebase credentials file not found: {FIREBASE_CREDENTIALS_PATH}")

# Initialize Firebase
cred = credentials.Certificate(FIREBASE_CREDENTIALS_PATH)
firebase_admin.initialize_app(cred)

# Firestore DB instance
db = firestore.client()