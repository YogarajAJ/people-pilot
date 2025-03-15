from flask import request
from flask_restful import Resource
from server.firestore import FirestoreDB
from datetime import datetime
import uuid
from utils.response_wrapper import response_wrapper

db = FirestoreDB()

class AttendanceAPI(Resource):
    def post(self):
        """Clock-In / Clock-Out API (Single Endpoint)"""
        try:
            data = request.get_json()
            if not data or "Employee_id" not in data or "clock_in" not in data:
                return response_wrapper(400, "Employee_id and clock_in flag are required", None)

            employee_id = data["Employee_id"]
            is_clock_in = data["clock_in"]  # True for clock-in, False for clock-out
            timestamp = datetime.utcnow().isoformat()

            if is_clock_in:
                # Clock-In logic
                entry = {
                    "id": str(uuid.uuid4()),
                    "Employee_id": employee_id,
                    "clock_in": timestamp,
                    "clock_out": None,
                    "date": datetime.utcnow().date().isoformat(),
                    "created_date": timestamp,
                    "last_modified_date": timestamp,
                }
            else:
                # Clock-Out logic: Find last clock-in record
                records = db.get_records(employee_id)
                if not records or records[-1].get("clock_out"):
                    return response_wrapper(400, "No active clock-in record found", None)

                entry = records[-1]
                entry["clock_out"] = timestamp
                entry["last_modified_date"] = timestamp

            db.add_record(entry)
            return response_wrapper(200, "Attendance recorded successfully", entry)

        except Exception as e:
            return response_wrapper(500, str(e), None)

    def get(self):
        """Get Attendance Records"""
        try:
            employee_id = request.args.get("Employee_id")
            if not employee_id:
                return response_wrapper(400, "Employee_id is required", None)

            records = db.get_records(employee_id)
            return response_wrapper(200, "Records fetched", records)

        except Exception as e:
            return response_wrapper(500, str(e), None)
