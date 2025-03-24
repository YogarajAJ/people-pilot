import os
import json
import firebase_admin
from firebase_admin import credentials, firestore

# Path for local development (when running with Docker)
FIREBASE_CREDENTIALS_PATH = "/serviceAccountKey.json"

# Check if credentials are provided as environment variable (for Render.com)
FIREBASE_CREDENTIALS_JSON = os.environ.get("FIREBASE_CREDENTIALS_JSON")

try:
    # Try to use environment variable first
    if FIREBASE_CREDENTIALS_JSON:
        cred_dict = json.loads(FIREBASE_CREDENTIALS_JSON)
        cred = credentials.Certificate(cred_dict)
        firebase_admin.initialize_app(cred)
    # Fall back to file if environment variable is not set
    elif os.path.exists(FIREBASE_CREDENTIALS_PATH):
        cred = credentials.Certificate(FIREBASE_CREDENTIALS_PATH)
        firebase_admin.initialize_app(cred)
    else:
        raise FileNotFoundError(f"Firebase credentials file not found: {FIREBASE_CREDENTIALS_PATH}")

    db = firestore.client()
except Exception as e:
    print(f"Error initializing Firebase: {e}")
    raise