from config import db

class FirestoreDB:
    def __init__(self):
        self.db = db  # ✅ Use the already initialized Firestore client
        
    def add_document(self, collection, doc_id, data):
        self.db.collection(collection).document(doc_id).set(data)

    def get_document(self, collection, doc_id):
        doc = self.db.collection(collection).document(doc_id).get()
        return doc.to_dict() if doc.exists else None

    def get_all_documents(self, collection):
        docs = self.db.collection(collection).order_by('created_at', direction='DESCENDING').stream()
        return [doc.to_dict() for doc in docs]
        
    def get_document_by_field(self, collection, field_name, field_value):
        docs = self.db.collection(collection).where(field_name, "==", field_value).limit(1).stream()
        for doc in docs:
            return doc.to_dict()  # Return the first matching document
        return None  # Return None if no document found
    
    def update_document(self, collection, doc_id, data):
        """Update fields in a document"""
        self.db.collection(collection).document(doc_id).update(data)
        
    def delete_document(self, collection, doc_id):
        """Delete a document"""
        self.db.collection(collection).document(doc_id).delete()
        
    def get_documents_by_field(self, collection, field_name, field_value):
        """Get all documents matching a field value"""
        docs = self.db.collection(collection).where(field_name, "==", field_value).stream()
        return [doc.to_dict() for doc in docs]