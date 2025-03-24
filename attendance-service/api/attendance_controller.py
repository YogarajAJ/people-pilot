from flask import request
from flask_restful import Resource
from server.firestore import FirestoreDB
from datetime import datetime
import uuid
import logging
from geopy.distance import geodesic

from utils.response_wrapper import response_wrapper

db = FirestoreDB()

# Geofence location settings
OFFICE_LOCATION = (12.956203, 80.195962)  # Office latitude & longitude
ALLOWED_RADIUS_KM = 0.1  # Allowed radius (100 meters)

class AttendanceAPI(Resource):
    def post(self):
        """Clock-In / Clock-Out API"""
        try:
            data = request.get_json()
            if not data or "employee_id" not in data or "clock_in" not in data:
                return response_wrapper(400, "employee_id and clock_in flag are required", None)

            employee_id = data["employee_id"]
            is_clock_in = data["clock_in"]  # True for clock-in, False for clock-out
            latitude = data.get("latitude")
            longitude = data.get("longitude")

            if latitude is None or longitude is None:
                return response_wrapper(400, "Latitude and longitude are required", None)

            user_location = (latitude, longitude)
            timestamp = datetime.utcnow().isoformat()
            date_str = datetime.utcnow().date().isoformat()

            # Validate geofence location
            distance = geodesic(OFFICE_LOCATION, user_location).km
            attendance_status = "VALID"
            
            if distance > ALLOWED_RADIUS_KM:
                attendance_status = "INVALID_LOCATION"
                logging.info(f"Employee {employee_id} outside location: {distance:.2f} km away")
                
                # We're still recording the attempt but marking it as invalid
                # Instead of returning a 403, we'll allow the record but mark its status

            # Fetch attendance collection for the employee and date
            entry_id = str(uuid.uuid4())

            if is_clock_in:
                entry = {
                    "id": entry_id,
                    "employee_id": employee_id,
                    "clock_in": timestamp,
                    "clock_out": None,
                    "date": date_str,
                    "location": {
                        "latitude": latitude,
                        "longitude": longitude,
                        "distance_km": distance,
                        "type": "clock_in"
                    },
                    "status": attendance_status,
                    "created_date": timestamp,
                    "last_modified_date": timestamp
                }
                db.add_record(entry)
            else:
                # Clock-Out: Find last clock-in record
                records = db.get_records_by_date(employee_id, date_str)
                active_records = [r for r in records if r["clock_out"] is None]

                if not active_records:
                    return response_wrapper(400, "No active clock-in record found", None)

                entry = active_records[-1]  # Get last clock-in
                entry["clock_out"] = timestamp
                entry["clock_out_location"] = {
                    "latitude": latitude,
                    "longitude": longitude,
                    "distance_km": distance,
                    "type": "clock_out"
                }
                entry["clock_out_status"] = attendance_status
                entry["last_modified_date"] = timestamp

                db.add_record(entry)

            return response_wrapper(200, "Attendance recorded successfully", entry)

        except Exception as e:
            logging.error(f"Error in AttendanceAPI: {str(e)}")
            return response_wrapper(500, str(e), None)


class AttendanceByDateAPI(Resource):
    def get(self):
        """Fetch Attendance Records for a Specific Date"""
        try:
            employee_id = request.args.get("employee_id")
            date_str = request.args.get("date")  # Expected format: YYYY-MM-DD

            if not date_str:
                return response_wrapper(400, "date parameter is required", None)

            # If employee_id is provided, get records for that employee on that date
            if employee_id:
                records = db.get_records_by_date(employee_id, date_str)
                if not records:
                    return response_wrapper(404, f"No records found for employee {employee_id} on {date_str}", None)
                return response_wrapper(200, "Records fetched", records)
            
            # If no employee_id is provided, get records for all employees on that date
            else:
                records = db.get_all_records_by_date(date_str)
                if not records:
                    return response_wrapper(404, f"No attendance records found for {date_str}", None)
                return response_wrapper(200, "Records fetched", records)

        except Exception as e:
            logging.error(f"Error fetching attendance records: {str(e)}")
            return response_wrapper(500, str(e), None)


class EmployeeAttendanceAPI(Resource):
    def get(self, employee_id):
        """Fetch Attendance History for a Specific Employee"""
        try:
            start_date = request.args.get("start_date")  # Optional: YYYY-MM-DD
            end_date = request.args.get("end_date")      # Optional: YYYY-MM-DD

            if not employee_id:
                return response_wrapper(400, "employee_id is required", None)

            records = db.get_employee_attendance_history(employee_id, start_date, end_date)
            
            if not records:
                message = "No attendance records found"
                if start_date and end_date:
                    message += f" between {start_date} and {end_date}"
                elif start_date:
                    message += f" from {start_date} onwards"
                elif end_date:
                    message += f" up to {end_date}"
                    
                return response_wrapper(404, message, None)

            return response_wrapper(200, "Attendance history fetched", records)

        except Exception as e:
            logging.error(f"Error fetching employee attendance history: {str(e)}")
            return response_wrapper(500, str(e), None)