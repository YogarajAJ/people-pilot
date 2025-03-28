from flask import request
from flask_restful import Resource
from server.firestore import FirestoreDB
from datetime import datetime
import uuid
import logging
from geopy.distance import geodesic
from config import db

from utils.response_wrapper import response_wrapper

# Initialize database
db_instance = FirestoreDB()

# App Config Collection
APP_CONFIG_COLLECTION = "app_configs"
DEFAULT_CONFIG_ID = "default_config"

# Default configuration values (used as fallback)
DEFAULT_OFFICE_LOCATION = (12.956203, 80.195962)  # Office latitude & longitude
DEFAULT_ALLOWED_RADIUS_KM = 0.1  # Allowed radius (100 meters)

# Attendance logs for rejected attempts
ATTENDANCE_LOGS_COLLECTION = "attendance_logs"

def get_app_config():
    """Get application configuration for office location and geofence settings"""
    try:
        # Try to get existing configuration
        config_ref = db.collection(APP_CONFIG_COLLECTION).document(DEFAULT_CONFIG_ID)
        config = config_ref.get()
        
        # If config exists, return it
        if config.exists:
            return config.to_dict()
            
        # If no config found, create default
        default_config = {
            "id": DEFAULT_CONFIG_ID,
            "office_location": {
                "latitude": DEFAULT_OFFICE_LOCATION[0],
                "longitude": DEFAULT_OFFICE_LOCATION[1]
            },
            "allowed_radius_km": DEFAULT_ALLOWED_RADIUS_KM,
            "enforce_geofence": True,
            "created_at": datetime.utcnow().isoformat(),
            "last_modified": datetime.utcnow().isoformat(),
            "last_modified_by": "system"
        }
        
        # Store default configuration
        config_ref.set(default_config)
        return default_config
        
    except Exception as e:
        logging.error(f"Error retrieving app configuration: {str(e)}")
        # Return default config if there's an error
        return {
            "office_location": {
                "latitude": DEFAULT_OFFICE_LOCATION[0],
                "longitude": DEFAULT_OFFICE_LOCATION[1]
            },
            "allowed_radius_km": DEFAULT_ALLOWED_RADIUS_KM,
            "enforce_geofence": True
        }

def add_attendance_log(log_data):
    """Add a rejected attendance attempt to logs"""
    try:
        db.collection(ATTENDANCE_LOGS_COLLECTION).document(log_data["id"]).set(log_data)
        return True
    except Exception as e:
        logging.error(f"Error adding attendance log: {str(e)}")
        return False


class AttendanceAPI(Resource):
    def post(self):
        """Clock-In / Clock-Out API with geofence validation"""
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

            # Get application configuration
            app_config = get_app_config()
            
            # Extract configuration values with fallbacks
            office_location = (
                app_config.get("office_location", {}).get("latitude", DEFAULT_OFFICE_LOCATION[0]),
                app_config.get("office_location", {}).get("longitude", DEFAULT_OFFICE_LOCATION[1])
            )
            allowed_radius_km = app_config.get("allowed_radius_km", DEFAULT_ALLOWED_RADIUS_KM)
            enforce_geofence = app_config.get("enforce_geofence", True)

            # Validate geofence location
            distance = geodesic(office_location, user_location).km
            
            # Determine attendance status
            if distance <= allowed_radius_km:
                attendance_status = "VALID"
            else:
                attendance_status = "INVALID_LOCATION"
                logging.info(f"Employee {employee_id} outside location: {distance:.2f} km away")
                
                # If geofence is enforced, reject the attendance record
                if enforce_geofence:
                    # Create log entry for the rejected attempt
                    log_entry = {
                        "id": str(uuid.uuid4()),
                        "employee_id": employee_id,
                        "timestamp": timestamp,
                        "date": date_str,
                        "action": "clock_in" if is_clock_in else "clock_out",
                        "location": {
                            "latitude": latitude,
                            "longitude": longitude,
                            "distance_km": distance
                        },
                        "status": "REJECTED",
                        "reason": f"Outside permitted radius ({distance:.2f} km from office)"
                    }
                    
                    # Store the log entry
                    add_attendance_log(log_entry)
                    
                    return response_wrapper(403, 
                        f"Attendance rejected: You are {distance:.2f} km from the office, which exceeds the allowed radius of {allowed_radius_km} km",
                        log_entry)

            # Generate a unique ID for this attendance record
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
                db_instance.add_record(entry)
            else:
                # Clock-Out: Find last clock-in record
                records = db_instance.get_records_by_date(employee_id, date_str)
                active_records = [r for r in records if r.get("clock_out") is None]

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

                db_instance.add_record(entry)

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
                records = db_instance.get_records_by_date(employee_id, date_str)
                if not records:
                    return response_wrapper(404, f"No records found for employee {employee_id} on {date_str}", None)
                return response_wrapper(200, "Records fetched", records)
            
            # If no employee_id is provided, get records for all employees on that date
            else:
                records = db_instance.get_all_records_by_date(date_str)
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

            records = db_instance.get_employee_attendance_history(employee_id, start_date, end_date)
            
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


class AttendanceLogsAPI(Resource):
    def get(self):
        """Fetch Rejected Attendance Logs"""
        try:
            employee_id = request.args.get("employee_id")
            date_str = request.args.get("date")  # Expected format: YYYY-MM-DD
            limit = int(request.args.get("limit", 100))
            
            query = db.collection(ATTENDANCE_LOGS_COLLECTION)
            
            # Apply filters if provided
            if employee_id:
                query = query.where("employee_id", "==", employee_id)
                
            if date_str:
                query = query.where("date", "==", date_str)
                
            # Order by timestamp (newest first) and limit results
            query = query.order_by("timestamp", direction="DESCENDING").limit(limit)
            
            # Execute query
            logs = [doc.to_dict() for doc in query.stream()]
            
            return response_wrapper(200, "Attendance logs retrieved", logs)
            
        except Exception as e:
            logging.error(f"Error fetching attendance logs: {str(e)}")
            return response_wrapper(500, str(e), None)


class AppConfigAPI(Resource):
    def get(self):
        """Retrieve application configuration"""
        try:
            config = get_app_config()
            return response_wrapper(200, "Application configuration retrieved successfully", config)
        except Exception as e:
            logging.error(f"Error retrieving app configuration: {str(e)}")
            return response_wrapper(500, str(e), None)
    
    def put(self):
        """Update application configuration"""
        try:
            data = request.get_json()
            admin_id = request.headers.get("X-Admin-ID", "admin")  # Optional admin identifier
            
            if not data:
                return response_wrapper(400, "No configuration data provided", None)
                
            # Validate required fields
            if "office_location" in data:
                location_data = data["office_location"]
                if not isinstance(location_data, dict) or "latitude" not in location_data or "longitude" not in location_data:
                    return response_wrapper(400, "Invalid office location format. Must include latitude and longitude", None)
                
                # Validate latitude and longitude values
                try:
                    latitude = float(location_data["latitude"])
                    longitude = float(location_data["longitude"])
                    
                    if latitude < -90 or latitude > 90:
                        return response_wrapper(400, "Invalid latitude value. Must be between -90 and 90", None)
                    if longitude < -180 or longitude > 180:
                        return response_wrapper(400, "Invalid longitude value. Must be between -180 and 180", None)
                except ValueError:
                    return response_wrapper(400, "Latitude and longitude must be valid numbers", None)
            
            # Validate radius if provided
            if "allowed_radius_km" in data:
                try:
                    radius = float(data["allowed_radius_km"])
                    if radius <= 0:
                        return response_wrapper(400, "Allowed radius must be greater than 0", None)
                except ValueError:
                    return response_wrapper(400, "Allowed radius must be a valid number", None)
            
            # Get current configuration
            config_ref = db.collection(APP_CONFIG_COLLECTION).document(DEFAULT_CONFIG_ID)
            config = config_ref.get()
            
            # If no config exists, create default first
            if not config.exists:
                current_config = get_app_config()  # This will create the default
            else:
                current_config = config.to_dict()
            
            # Update fields
            updated_config = current_config.copy()
            
            if "office_location" in data:
                updated_config["office_location"] = data["office_location"]
                
            if "allowed_radius_km" in data:
                updated_config["allowed_radius_km"] = float(data["allowed_radius_km"])
                
            if "enforce_geofence" in data:
                updated_config["enforce_geofence"] = bool(data["enforce_geofence"])
            
            # Add metadata
            updated_config["last_modified"] = datetime.utcnow().isoformat()
            updated_config["last_modified_by"] = admin_id
            
            # Save the updated configuration
            config_ref.set(updated_config)
            
            return response_wrapper(200, "Application configuration updated successfully", updated_config)
            
        except Exception as e:
            logging.error(f"Error updating app configuration: {str(e)}")
            return response_wrapper(500, str(e), None)