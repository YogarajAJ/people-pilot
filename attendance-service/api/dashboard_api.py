from flask import request
from flask_restful import Resource
from datetime import datetime, timedelta
import requests
import logging
import os
from utils.response_wrapper import response_wrapper
from server.firestore import FirestoreDB

# API endpoints
EMPLOYEE_SERVICE_URL = os.environ.get('EMPLOYEE_SERVICE_URL', 'http://localhost:5002')

# Create db instance
db = FirestoreDB()

class DashboardAPI(Resource):
    def get(self):
        """
        Get dashboard data including:
        - Total employees count
        - Present/Late/Absent counts for today
        - Recent activity log
        - Weekly attendance overview
        
        Query parameters:
        - date: Optional date (YYYY-MM-DD) - defaults to today
        """
        try:
            # Get date parameter or use today
            date_str = request.args.get("date")
            if not date_str:
                date_str = datetime.utcnow().date().isoformat()
                
            # Get employees from employee service
            try:
                response = requests.get(f"{EMPLOYEE_SERVICE_URL}/api/employee/all")
                if response.status_code != 200:
                    return response_wrapper(500, f"Failed to fetch employees: {response.status_code}", None)
                
                employees_data = response.json()
                if employees_data.get("status") != 200:
                    return response_wrapper(500, f"Employee API error: {employees_data.get('message')}", None)
                
                all_employees = employees_data.get("data", [])
                total_employees = len(all_employees)
                
                if total_employees == 0:
                    return response_wrapper(200, "No employees found", {
                        "attendance_summary": {
                            "date": date_str,
                            "total_employees": 0,
                            "present_count": 0,
                            "late_count": 0,
                            "absent_count": 0,
                            "present_percentage": 0,
                            "late_percentage": 0,
                            "absent_percentage": 0
                        },
                        "recent_activity": [],
                        "weekly_overview": []
                    })
                
            except Exception as e:
                logging.error(f"Error fetching employees: {str(e)}")
                return response_wrapper(500, f"Error fetching employees: {str(e)}", None)
            
            # Get today's attendance records directly from database
            today_records = db.get_all_records_by_date(date_str)
            
            # Calculate attendance stats
            on_time_count = 0
            late_count = 0
            present_employee_ids = set()
            
            for record in today_records:
                employee_id = record.get("employee_id")
                if employee_id:
                    present_employee_ids.add(employee_id)
                    
                    # Check if employee was late (clock_in after 9:30 AM)
                    clock_in_time = record.get("clock_in")
                    if clock_in_time:
                        try:
                            clock_in_dt = datetime.fromisoformat(clock_in_time)
                            clock_in_hour = clock_in_dt.hour
                            clock_in_minute = clock_in_dt.minute
                            
                            # Consider late if arrived after 9:30 AM
                            if clock_in_hour > 9 or (clock_in_hour == 9 and clock_in_minute > 30):
                                late_count += 1
                            else:
                                on_time_count += 1
                        except ValueError:
                            # If time cannot be parsed, count as on time
                            on_time_count += 1
                    else:
                        # If no clock_in time, count as on time
                        on_time_count += 1
            
            # Calculate total present and absent employees
            present_count = len(present_employee_ids)  # Total number of employees who are present
            absent_count = total_employees - present_count
            
            # Make sure our calculations are accurate
            if on_time_count + late_count != present_count:
                logging.warning(f"Attendance count mismatch: on_time({on_time_count}) + late({late_count}) != present({present_count})")
                # Adjust on_time to ensure totals match
                on_time_count = present_count - late_count
            
            # Get recent activity (last 5 clock events)
            recent_activity = []
            sorted_records = sorted(today_records, key=lambda x: x.get("last_modified_date", ""), reverse=True)
            
            for record in sorted_records[:5]:
                employee_id = record.get("employee_id")
                employee_info = next((e for e in all_employees if e.get("id") == employee_id), {})
                
                has_clock_in = record.get("clock_in") is not None
                has_clock_out = record.get("clock_out") is not None
                
                # Determine the most recent event (clock in or clock out)
                is_clock_out = has_clock_out and record.get("clock_out") != ""
                event_time = record.get("clock_out") if is_clock_out else record.get("clock_in")
                
                if event_time:
                    try:
                        event_dt = datetime.fromisoformat(event_time)
                        formatted_time = event_dt.strftime("%H:%M")
                        
                        activity = {
                            "employee_id": employee_id,
                            "name": employee_info.get("name", "Unknown Employee"),
                            "action": "clocked out" if is_clock_out else "clocked in",
                            "time": formatted_time,
                            "is_late": False
                        }
                        
                        # If it's a clock-in event, check if it was late
                        if not is_clock_out:
                            if event_dt.hour > 9 or (event_dt.hour == 9 and event_dt.minute > 30):
                                activity["is_late"] = True
                                activity["action"] = "arrived late"
                        
                        recent_activity.append(activity)
                    except ValueError:
                        pass
            
            # Get weekly attendance overview (for the past 7 days)
            weekly_data = []
            end_date = datetime.strptime(date_str, "%Y-%m-%d").date()
            start_date = end_date - timedelta(days=6)  # 7 days including today
            
            # Process each day in the range manually
            current_date = start_date
            while current_date <= end_date:
                current_date_str = current_date.isoformat()
                day_records = db.get_all_records_by_date(current_date_str)
                
                # Count present employees for this day
                day_present_count = len(set(record.get("employee_id") for record in day_records))
                
                # Format data for chart
                display_date = current_date.strftime("%a")  # Short day name
                weekly_data.append({
                    "date": current_date_str,
                    "display_date": display_date,
                    "present": day_present_count,
                    "total": total_employees
                })
                
                # Move to next day
                current_date += timedelta(days=1)
            
            # Calculate accurate percentages
            present_percentage = round((present_count / total_employees * 100), 1) if total_employees > 0 else 0
            late_percentage = round((late_count / total_employees * 100), 1) if total_employees > 0 else 0
            absent_percentage = round((absent_count / total_employees * 100), 1) if total_employees > 0 else 0
            
            # Build dashboard data
            dashboard_data = {
                "attendance_summary": {
                    "date": date_str,
                    "total_employees": total_employees,
                    "present_count": on_time_count,
                    "late_count": late_count,
                    "absent_count": absent_count,
                    "present_percentage": present_percentage,
                    "late_percentage": late_percentage,
                    "absent_percentage": absent_percentage
                },
                "recent_activity": recent_activity,
                "weekly_overview": weekly_data
            }
            
            return response_wrapper(200, "Dashboard data retrieved successfully", dashboard_data)
            
        except Exception as e:
            logging.error(f"Error generating dashboard data: {str(e)}")
            return response_wrapper(500, str(e), None)