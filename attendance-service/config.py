import os
import firebase_admin
from firebase_admin import credentials, firestore

# Define the local path to your Firebase service account key
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FIREBASE_CREDENTIALS_PATH = os.path.join(BASE_DIR, "serviceAccountKey.json")

# Initialize Firebase
cred = credentials.Certificate(FIREBASE_CREDENTIALS_PATH)
firebase_admin.initialize_app(cred)

# Firestore DB instance
db = firestore.client()
