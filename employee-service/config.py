import os
import firebase_admin
from firebase_admin import credentials, firestore

# Get the absolute path of the service account key in the root directory
FIREBASE_CREDENTIALS_PATH = os.getenv("FIREBASE_CREDENTIALS", "/serviceAccountKey.json")

# Check if the file exists before initializing Firebase
if not os.path.exists(FIREBASE_CREDENTIALS_PATH):
    raise FileNotFoundError(f"Firebase credentials file not found: {FIREBASE_CREDENTIALS_PATH}")

# Initialize Firebase
cred = credentials.Certificate(FIREBASE_CREDENTIALS_PATH)
firebase_admin.initialize_app(cred)

# Firestore DB instance
db = firestore.client()
