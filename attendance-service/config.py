import os
import firebase_admin
from firebase_admin import credentials, firestore

# Get the absolute path of the service account key in the root directory
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # people-pilot/
FIREBASE_CREDENTIALS_PATH = os.path.join(BASE_DIR, "serviceAccountKey.json")

# Check if the file exists before initializing Firebase
if not os.path.exists(FIREBASE_CREDENTIALS_PATH):
    raise FileNotFoundError(f"Firebase credentials file not found: {FIREBASE_CREDENTIALS_PATH}")

# Initialize Firebase
cred = credentials.Certificate(FIREBASE_CREDENTIALS_PATH)
firebase_admin.initialize_app(cred)

# Firestore DB instance
db = firestore.client()
