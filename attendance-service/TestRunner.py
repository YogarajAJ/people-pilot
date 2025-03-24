import requests
import random
import json
import time
from datetime import datetime, timedelta

# API endpoints
EMPLOYEE_API_URL = "http://127.0.0.1:5002/api/employee"
ATTENDANCE_API_URL = "http://localhost:5003/api/attendance"

# Office coordinates (used by the geofencing system)
OFFICE_LOCATION = (12.956203, 80.195962)  # Office latitude & longitude
ALLOWED_RADIUS_KM = 0.1  # 100 meters (matches server setting)

def fetch_all_employees():
    """Fetch all employees from the API"""
    try:
        response = requests.get(f"{EMPLOYEE_API_URL}/all")
        if response.status_code == 200:
            result = response.json()
            if result["status"] == 200:
                return result["data"]
            else:
                print(f"API error: {result['message']}")
        else:
            print(f"HTTP error: {response.status_code}")
    except Exception as e:
        print(f"Exception fetching employees: {str(e)}")
    
    return []

def generate_location(is_valid=True):
    """Generate a random location within or outside the office radius"""
    base_lat, base_lng = OFFICE_LOCATION
    
    if is_valid:
        # Within the allowed radius (with some variation but still valid)
        max_offset = ALLOWED_RADIUS_KM * 0.8 / 111.32  # Convert km to approx. degrees, stay inside 80% of limit
        lat_offset = random.uniform(-max_offset, max_offset)
        lng_offset = random.uniform(-max_offset, max_offset)
    else:
        # Outside the allowed radius (but not too far)
        min_offset = ALLOWED_RADIUS_KM * 1.2 / 111.32  # Just outside the limit
        max_offset = ALLOWED_RADIUS_KM * 5 / 111.32    # Not more than 5x the limit
        lat_offset = random.uniform(min_offset, max_offset) * random.choice([-1, 1])
        lng_offset = random.uniform(min_offset, max_offset) * random.choice([-1, 1])
    
    return {
        "latitude": base_lat + lat_offset,
        "longitude": base_lng + lng_offset
    }

def generate_attendance_for_date(date_str, employees, attendance_rate=0.85):
    """Generate attendance data for a specific date"""
    print(f"\nGenerating attendance for date: {date_str}")
    
    for employee in employees:
        # Randomly decide if employee is present (based on attendance rate)
        if random.random() < attendance_rate:
            employee_id = employee["id"]
            
            # Randomly decide if location is valid (85% chance of being valid)
            is_valid_location = random.random() < 0.85
            
            # Generate clock-in data
            clock_in_time = f"{date_str}T{random.randint(8, 10):02d}:{random.randint(0, 59):02d}:00"
            clock_in_location = generate_location(is_valid_location)
            
            clock_in_data = {
                "employee_id": employee_id,
                "clock_in": True,
                "latitude": clock_in_location["latitude"],
                "longitude": clock_in_location["longitude"]
            }
            
            # Send clock-in request
            try:
                response = requests.post(
                    ATTENDANCE_API_URL,
                    json=clock_in_data,
                    headers={"Content-Type": "application/json"}
                )
                
                if response.status_code == 200:
                    result = response.json()
                    if result["status"] == 200:
                        print(f"  ✓ Created clock-in for {employee_id} ({employee['name']}) - Status: {result['data']['status']}")
                        
                        # Generate clock-out data (only if clock-in was successful)
                        # Clock out between 5pm and 7pm
                        clock_out_time = f"{date_str}T{random.randint(17, 19):02d}:{random.randint(0, 59):02d}:00"
                        
                        # Usually same location validity as clock-in, but occasionally different
                        is_valid_location_out = is_valid_location
                        if random.random() < 0.1:  # 10% chance of different status
                            is_valid_location_out = not is_valid_location
                        
                        clock_out_location = generate_location(is_valid_location_out)
                        
                        clock_out_data = {
                            "employee_id": employee_id,
                            "clock_in": False,
                            "latitude": clock_out_location["latitude"],
                            "longitude": clock_out_location["longitude"]
                        }
                        
                        # Add a delay to ensure clock-out is after clock-in
                        time.sleep(0.5)
                        
                        # Send clock-out request
                        try:
                            response = requests.post(
                                ATTENDANCE_API_URL,
                                json=clock_out_data,
                                headers={"Content-Type": "application/json"}
                            )
                            
                            if response.status_code == 200:
                                result = response.json()
                                if result["status"] == 200:
                                    print(f"  ✓ Created clock-out for {employee_id} ({employee['name']}) - Status: {result['data']['clock_out_status']}")
                                else:
                                    print(f"  ✗ Clock-out API error: {result['message']}")
                            else:
                                print(f"  ✗ Clock-out HTTP error: {response.status_code}")
                        except Exception as e:
                            print(f"  ✗ Exception during clock-out: {str(e)}")
                    else:
                        print(f"  ✗ Clock-in API error: {result['message']}")
                else:
                    print(f"  ✗ Clock-in HTTP error: {response.status_code}")
            except Exception as e:
                print(f"  ✗ Exception during clock-in: {str(e)}")
            
            # Add a delay before processing the next employee
            time.sleep(0.2)
        else:
            print(f"  - Employee {employee['id']} ({employee['name']}) absent")
    
    print(f"Completed attendance generation for {date_str}")

def main():
    """Main function"""
    print("Attendance Data Generator")
    print("========================\n")
    
    # Fetch all employees
    print("Fetching employees...")
    employees = fetch_all_employees()
    
    if not employees:
        print("No employees found. Please create employees first.")
        return
    
    print(f"Found {len(employees)} employees")
    
    # Ask for date range
    try:
        days_back = int(input("How many days of attendance data to generate (default: 7)? ") or "7")
    except ValueError:
        days_back = 7
        print("Invalid input. Using default value of 7 days.")
    
    # Ask for attendance rate
    try:
        attendance_rate = float(input("What percentage of employees should be present each day (0-100, default: 85)? ") or "85") / 100
        attendance_rate = max(0, min(1, attendance_rate))  # Ensure between 0 and 1
    except ValueError:
        attendance_rate = 0.85
        print("Invalid input. Using default value of 85%.")
    
    # Generate data for each day
    today = datetime.now().date()
    
    for day_offset in range(days_back - 1, -1, -1):  # Start from oldest to newest
        target_date = today - timedelta(days=day_offset)
        date_str = target_date.isoformat()
        
        generate_attendance_for_date(date_str, employees, attendance_rate)
        
        # Add a delay between days
        if day_offset > 0:
            time.sleep(1)
    
    print("\nAttendance data generation complete!")
    print(f"Generated data for {len(employees)} employees across {days_back} days")
    print(f"Expected attendance rate: {attendance_rate:.1%}")

if __name__ == "__main__":
    main()