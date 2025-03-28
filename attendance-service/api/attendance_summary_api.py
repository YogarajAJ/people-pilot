from flask import request
from flask_restful import Resource
from server.firestore import FirestoreDB
from datetime import datetime, timedelta
import logging
import requests
import os
from utils.response_wrapper import response_wrapper

db = FirestoreDB()
EMPLOYEE_API_URL = os.environ.get('EMPLOYEE_SERVICE_URL', 'http://localhost:5002')


class AttendanceSummaryAPI(Resource):
    def get(self):
        """
        Get attendance summary for a specific date with present/absent employees
        
        Query parameters:
            date (str): Date in YYYY-MM-DD format (defaults to today)
            detailed (bool): Whether to include detailed employee information (default: false)
        """
        try:
            # Get date parameter or use today's date
            date_str = request.args.get("date")
            if not date_str:
                date_str = datetime.utcnow().date().isoformat()
            
            detailed = request.args.get("detailed", "false").lower() == "true"
            
            # Get all attendance records for the date
            attendance_records = db.get_all_records_by_date(date_str)
            
            # Get all employees from the employee service
            try:
                response = requests.get(f"{EMPLOYEE_API_URL}/api/employee/all")
                if response.status_code != 200:
                    return response_wrapper(500, f"Failed to fetch employees: {response.status_code}", None)
                
                employees_data = response.json()
                if employees_data.get("status") != 200:
                    return response_wrapper(500, f"Employee API error: {employees_data.get('message')}", None)
                
                all_employees = employees_data.get("data", [])
            except Exception as e:
                logging.error(f"Error fetching employees: {str(e)}")
                return response_wrapper(500, f"Error fetching employees: {str(e)}", None)
            
            # Calculate summary statistics
            total_employees = len(all_employees)
            present_employee_ids = set(record.get("employee_id") for record in attendance_records)
            present_count = len(present_employee_ids)
            absent_count = total_employees - present_count
            
            # Create lists of present and absent employees with details
            present_employees = []
            absent_employees = []
            
            # Process present employees
            for record in attendance_records:
                employee_id = record.get("employee_id")
                employee_info = next((emp for emp in all_employees if emp.get("id") == employee_id), {})
                
                present_data = {
                    "employee_id": employee_id,
                    "name": employee_info.get("name", "Unknown"),
                    "clock_in_time": record.get("clock_in"),
                    "clock_out_time": record.get("clock_out"),
                    "status": record.get("status"),
                    "clock_out_status": record.get("clock_out_status"),
                    "within_office": record.get("status") == "VALID"
                }
                
                if detailed:
                    present_data["location"] = record.get("location")
                    present_data["clock_out_location"] = record.get("clock_out_location")
                    present_data["employee_details"] = employee_info
                
                present_employees.append(present_data)
            
            # Process absent employees
            for employee in all_employees:
                employee_id = employee.get("id")
                if employee_id not in present_employee_ids:
                    absent_data = {
                        "employee_id": employee_id,
                        "name": employee.get("name", "Unknown")
                    }
                    
                    if detailed:
                        absent_data["employee_details"] = employee
                    
                    absent_employees.append(absent_data)
            
            # Sort employees by name
            present_employees.sort(key=lambda x: x.get("name", ""))
            absent_employees.sort(key=lambda x: x.get("name", ""))
            
            # Calculate location statistics
            valid_location_count = sum(1 for record in attendance_records 
                                    if record.get("status") == "VALID")
            invalid_location_count = present_count - valid_location_count
            
            # Create summary object
            summary = {
                "date": date_str,
                "total_employees": total_employees,
                "present_count": present_count,
                "absent_count": absent_count,
                "attendance_percentage": round((present_count / total_employees * 100), 2) if total_employees > 0 else 0,
                "within_office_count": valid_location_count,
                "outside_office_count": invalid_location_count,
                "present_employees": present_employees,
                "absent_employees": absent_employees
            }
            
            return response_wrapper(200, "Attendance summary generated successfully", summary)
            
        except Exception as e:
            logging.error(f"Error generating attendance summary: {str(e)}")
            return response_wrapper(500, str(e), None)


class AttendanceRangeAPI(Resource):
    def get(self):
        """
        Get attendance summary for a date range
        
        Query parameters:
            start_date (str): Start date in YYYY-MM-DD format (required)
            end_date (str): End date in YYYY-MM-DD format (defaults to today)
        """
        try:
            # Get date parameters
            start_date = request.args.get("start_date")
            end_date = request.args.get("end_date")
            
            if not start_date:
                return response_wrapper(400, "start_date parameter is required", None)
            
            if not end_date:
                end_date = datetime.utcnow().date().isoformat()
            
            # Validate date format
            try:
                start_date_obj = datetime.strptime(start_date, "%Y-%m-%d").date()
                end_date_obj = datetime.strptime(end_date, "%Y-%m-%d").date()
            except ValueError:
                return response_wrapper(400, "Invalid date format. Use YYYY-MM-DD", None)
            
            # Ensure start_date is before or equal to end_date
            if start_date_obj > end_date_obj:
                return response_wrapper(400, "start_date must be before or equal to end_date", None)
            
            # Get all employees from the employee service
            try:
                response = requests.get(f"{EMPLOYEE_API_URL}/api/employee/all")
                if response.status_code != 200:
                    return response_wrapper(500, f"Failed to fetch employees: {response.status_code}", None)
                
                employees_data = response.json()
                if employees_data.get("status") != 200:
                    return response_wrapper(500, f"Employee API error: {employees_data.get('message')}", None)
                
                all_employees = employees_data.get("data", [])
                total_employees = len(all_employees)
            except Exception as e:
                logging.error(f"Error fetching employees: {str(e)}")
                return response_wrapper(500, f"Error fetching employees: {str(e)}", None)
            
            # Generate a list of all dates in the range
            date_list = []
            current_date = start_date_obj
            while current_date <= end_date_obj:
                date_list.append(current_date.isoformat())
                current_date += timedelta(days=1)
            
            # Create daily summaries
            daily_summaries = []
            
            for date_str in date_list:
                # Get attendance records for this date
                attendance_records = db.get_all_records_by_date(date_str)
                
                # Calculate summary statistics
                present_employee_ids = set(record.get("employee_id") for record in attendance_records)
                present_count = len(present_employee_ids)
                absent_count = total_employees - present_count
                
                # Calculate location statistics
                valid_location_count = sum(1 for record in attendance_records 
                                        if record.get("status") == "VALID")
                invalid_location_count = present_count - valid_location_count
                
                # Create summary for this date
                daily_summary = {
                    "date": date_str,
                    "total_employees": total_employees,
                    "present_count": present_count,
                    "absent_count": absent_count,
                    "attendance_percentage": round((present_count / total_employees * 100), 2) if total_employees > 0 else 0,
                    "within_office_count": valid_location_count,
                    "outside_office_count": invalid_location_count
                }
                
                daily_summaries.append(daily_summary)
            
            # Calculate overall statistics
            total_days = len(daily_summaries)
            avg_attendance_percentage = sum(day["attendance_percentage"] for day in daily_summaries) / total_days if total_days > 0 else 0
            
            # Create range summary
            range_summary = {
                "start_date": start_date,
                "end_date": end_date,
                "total_days": total_days,
                "total_employees": total_employees,
                "avg_attendance_percentage": round(avg_attendance_percentage, 2),
                "daily_summaries": daily_summaries
            }
            
            return response_wrapper(200, "Attendance range summary generated successfully", range_summary)
            
        except Exception as e:
            logging.error(f"Error generating attendance range summary: {str(e)}")
            return response_wrapper(500, str(e), None)