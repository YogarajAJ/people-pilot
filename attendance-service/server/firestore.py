from config import db

class FirestoreDB:
    def __init__(self):
        self.collection = db.collection("attendance")

    def add_record(self, data):
        doc_ref = self.collection.document(data["id"])
        doc_ref.set(data)
        return True

    def get_records(self, employee_id):
        docs = self.collection.where("Employee_id", "==", employee_id).stream()
        return [doc.to_dict() for doc in docs]
