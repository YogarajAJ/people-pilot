from flask import request
from flask_restful import Resource
from firestore import FirestoreDB
import uuid
from utils.response_wrapper import response_wrapper

db = FirestoreDB()

class EmployeeAPI(Resource):
    def post(self):
        """Add Employee API"""
        try:
            data = request.get_json()
            required_fields = ["name", "age", "date_of_birth", "email", "address", "blood_type", "phone_number", "designation", "ctc"]

            if not data or not all(k in data for k in required_fields):
                return response_wrapper(400, "Missing required fields", None)

            employee_id = str(uuid.uuid4())

            employee_data = {
                "id": employee_id,
                "name": data["name"],
                "age": data["age"],
                "date_of_birth": data["date_of_birth"],
                "email": data["email"],
                "address": data["address"],
                "blood_type": data["blood_type"],
                "phone_number": data["phone_number"],
                "designation": data["designation"],
                "ctc": data["ctc"]
            }

            db.add_document("employees", employee_id, employee_data)
            return response_wrapper(200, "Employee added", employee_data)

        except Exception as e:
            return response_wrapper(500, str(e), None)

    def get(self):
        """Get Employee API"""
        try:
            employee_id = request.args.get("id")
            if not employee_id:
                return response_wrapper(400, "Employee ID is required", None)

            employee = db.get_document("employees", employee_id)
            if not employee:
                return response_wrapper(404, "Employee not found", None)

            return response_wrapper(200, "Employee details fetched", employee)

        except Exception as e:
            return response_wrapper(500, str(e), None)

class EmployeeListAPI(Resource):
    def get(self):
        """Get All Employees API"""
        try:
            employees = db.get_all_documents("employees")
            return response_wrapper(200, "All employees fetched", employees)

        except Exception as e:
            return response_wrapper(500, str(e), None)
