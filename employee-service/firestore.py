import os
import firebase_admin
from firebase_admin import credentials, firestore

# Get the absolute path to the service account key
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # Get project root
FIREBASE_CREDENTIALS_PATH = os.path.join(BASE_DIR, "serviceAccountKey.json")

# Check if the file exists
if not os.path.exists(FIREBASE_CREDENTIALS_PATH):
    raise FileNotFoundError(f"Service account key not found: {FIREBASE_CREDENTIALS_PATH}")

# Initialize Firebase
cred = credentials.Certificate(FIREBASE_CREDENTIALS_PATH)
firebase_admin.initialize_app(cred)

# Firestore DB instance
db = firestore.client()

class FirestoreDB:
    def __init__(self):
        self.db = db  # ✅ Use the already initialized Firestore client
        
    def add_document(self, collection, doc_id, data):
        self.db.collection(collection).document(doc_id).set(data)

    def get_document(self, collection, doc_id):
        doc = self.db.collection(collection).document(doc_id).get()
        return doc.to_dict() if doc.exists else None

    def get_all_documents(self, collection):
        docs = self.db.collection(collection).stream()
        return [doc.to_dict() for doc in docs]
    def get_document_by_field(self, collection, field_name, field_value):
        docs = self.db.collection(collection).where(field_name, "==", field_value).stream()
        return [doc.to_dict() for doc in docs]
    

