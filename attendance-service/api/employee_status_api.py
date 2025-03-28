from flask import request
from flask_restful import Resource
from server.firestore import FirestoreDB
from datetime import datetime
import logging
from utils.response_wrapper import response_wrapper

# Initialize database
db_instance = FirestoreDB()

class EmployeeStatusAPI(Resource):
    def get(self):
        """
        Get the current attendance status of an employee (clocked-in or clocked-out)
        
        Query parameters:
            employee_id (str): The ID of the employee to check
        
        Returns:
            Status of the employee with details about their last attendance record
        """
        try:
            # Get employee_id from query parameters
            employee_id = request.args.get("employee_id")
            
            # Validate request
            if not employee_id:
                return response_wrapper(400, "employee_id query parameter is required", None)
                
            current_date = datetime.utcnow().date().isoformat()
            
            # Get today's attendance records for the employee
            records = db_instance.get_records_by_date(employee_id, current_date)
            
            # If no records found for today, employee hasn't clocked in
            if not records:
                return response_wrapper(200, "Employee has not clocked in today", {
                    "employee_id": employee_id,
                    "date": current_date,
                    "status": "NOT_CLOCKED_IN",
                    "last_action": None,
                    "last_action_time": None,
                    "location": None
                })
            
            # Sort records by last modified date (most recent first)
            sorted_records = sorted(
                records, 
                key=lambda x: x.get("last_modified_date", ""), 
                reverse=True
            )
            
            # Get the most recent record
            latest_record = sorted_records[0]
            
            # Determine if the employee is currently clocked in or out
            # If clock_out is None, employee is still clocked in
            is_clocked_in = latest_record.get("clock_out") is None
            
            if is_clocked_in:
                status = "CLOCKED_IN"
                last_action = "clock_in"
                last_action_time = latest_record.get("clock_in")
                location = latest_record.get("location")
            else:
                status = "CLOCKED_OUT"
                last_action = "clock_out"
                last_action_time = latest_record.get("clock_out")
                location = latest_record.get("clock_out_location")
            
            # Build response
            response_data = {
                "employee_id": employee_id,
                "date": current_date,
                "status": status,
                "last_action": last_action,
                "last_action_time": last_action_time,
                "location": location,
                "record_id": latest_record.get("id"),
                "status_valid": latest_record.get("status") if is_clocked_in else latest_record.get("clock_out_status")
            }
            
            return response_wrapper(200, f"Employee is currently {status.lower().replace('_', ' ')}", response_data)
            
        except Exception as e:
            error_message = f"Error fetching employee status: {str(e)}"
            logging.error(error_message)
            return response_wrapper(500, error_message, None)