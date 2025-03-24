import requests
import random
import json
import time
from datetime import datetime, timedelta
import sys

# API endpoint
API_URL = "http://127.0.0.1:5002/api/employee"

# Lists for generating random data
first_names = [
    "John", "Jane", "Michael", "Emily", "David", "Sarah", "Robert", "Lisa", 
    "William", "Emma", "James", "Olivia", "Benjamin", "Sophia", "Daniel", 
    "Ava", "Matthew", "Isabella", "Joseph", "Mia", "Andrew", "Charlotte", 
    "Raj", "Priya", "Amit", "Neha", "Wei", "Li", "Hiroshi", "Yuki"
]

last_names = [
    "Smith", "Johnson", "Williams", "Jones", "Brown", "Davis", "Miller", 
    "Wilson", "Moore", "Taylor", "Anderson", "Thomas", "Jackson", "White", 
    "Harris", "Martin", "Thompson", "Garcia", "Martinez", "Robinson", 
    "Patel", "Kumar", "Singh", "Shah", "Wang", "Chen", "Zhang", "Li", 
    "Tanaka", "Suzuki", "Sato", "Kim"
]

designations = [
    "Software Engineer", "Senior Software Engineer", "Lead Developer",
    "Full Stack Developer", "Frontend Developer", "Backend Developer",
    "DevOps Engineer", "QA Engineer", "UI/UX Designer", "Product Manager",
    "Project Manager", "Data Scientist", "Data Analyst", "Machine Learning Engineer",
    "Database Administrator", "Network Engineer", "System Administrator",
    "Technical Support", "IT Manager", "CTO", "HR Manager", "Finance Manager"
]

blood_types = ["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"]

shift_hours = [
    "9:00 AM - 6:00 PM",
    "10:00 AM - 7:00 PM",
    "8:00 AM - 5:00 PM",
    "7:00 AM - 4:00 PM",
    "11:00 AM - 8:00 PM"
]

addresses = [
    "123 Main St, New York, NY",
    "456 Oak Ave, Los Angeles, CA",
    "789 Pine Rd, Chicago, IL",
    "101 Maple Dr, Houston, TX",
    "202 Cedar Ln, Phoenix, AZ",
    "303 Elm Blvd, San Antonio, TX",
    "404 Birch Way, San Diego, CA",
    "505 Walnut Ct, Dallas, TX",
    "606 Cherry St, San Jose, CA",
    "707 Spruce Ave, Austin, TX"
]

def generate_random_employee_data(used_emails=None):
    """Generate random employee data with unique email"""
    if used_emails is None:
        used_emails = set()
    
    # Keep generating until we get a unique email
    while True:
        first_name = random.choice(first_names)
        last_name = random.choice(last_names)
        full_name = f"{first_name} {last_name}"
        
        # Create a unique email with timestamp
        timestamp = int(time.time() * 1000) + random.randint(1, 1000) 
        email = f"{first_name.lower()}.{last_name.lower()}.{timestamp}@example.com"
        
        if email not in used_emails:
            used_emails.add(email)
            break
    
    age = random.randint(22, 60)
    
    # Calculate date of birth based on age
    birth_year = datetime.now().year - age
    birth_month = random.randint(1, 12)
    birth_day = random.randint(1, 28)  # To avoid month-specific day validation
    date_of_birth = f"{birth_year}-{birth_month:02d}-{birth_day:02d}"
    
    return {
        "name": full_name,
        "age": age,
        "date_of_birth": date_of_birth,
        "email": email,
        "address": random.choice(addresses),
        "blood_type": random.choice(blood_types),
        "phone_number": f"+1-{random.randint(100, 999)}-{random.randint(100, 999)}-{random.randint(1000, 9999)}",
        "designation": random.choice(designations),
        "ctc": random.randint(50000, 150000),
        "password": "password123",  # Simple default password
        "employee_shift_hours": random.choice(shift_hours)
    }

def print_response(response):
    """Print a well-formatted response"""
    try:
        json_data = response.json()
        print(json.dumps(json_data, indent=2))
    except:
        print(response.text)

def create_employees(count=10):
    """Create specified number of random employees"""
    print(f"\nCreating {count} random employees...")
    created_employees = []
    used_emails = set()
    
    for i in range(count):
        try:
            print(f"\n--- Creating employee {i+1}/{count} ---")
            
            # Generate random employee data
            employee_data = generate_random_employee_data(used_emails)
            
            print(f"Generated data for: {employee_data['name']} ({employee_data['email']})")
            
            # Make API call to create employee
            response = requests.post(
                f"{API_URL}/register", 
                json=employee_data,
                headers={"Content-Type": "application/json"}
            )
            
            print(f"Response status code: {response.status_code}")
            
            # Print full response for debugging
            print("Full response:")
            print_response(response)
            
            if response.status_code in [200, 201]:
                result = response.json()
                if result["status"] in [200, 201]:
                    employee = result["data"]
                    print(f"✅ Created employee: {employee['name']} (ID: {employee['id']})")
                    created_employees.append(employee)
                else:
                    print(f"❌ API error: {result['message']}")
            else:
                print(f"❌ HTTP error: {response.status_code}")
            
            # Add a small delay between requests to avoid overwhelming the server
            time.sleep(1)
                
        except Exception as e:
            print(f"❌ Exception: {str(e)}")
    
    print(f"\nSummary: Successfully created {len(created_employees)} out of {count} requested employees")
    return created_employees

def fetch_existing_employees():
    """Fetch existing employees for reference"""
    try:
        print("\nFetching existing employees...")
        response = requests.get(f"{API_URL}/all")
        
        if response.status_code == 200:
            result = response.json()
            if result["status"] == 200:
                employees = result["data"]
                print(f"Found {len(employees)} existing employees")
                
                if employees:
                    print("\nExisting Employee IDs:")
                    for employee in employees:
                        print(f"  ID: {employee['id']} | Name: {employee['name']} | Email: {employee['email']}")
                
                return employees
            else:
                print(f"API error: {result['message']}")
        else:
            print(f"HTTP error: {response.status_code}")
            
    except Exception as e:
        print(f"Exception: {str(e)}")
    
    return []

def delete_all_employees():
    """Delete all existing employees (USE WITH CAUTION)"""
    employees = fetch_existing_employees()
    
    if not employees:
        print("No employees to delete.")
        return
    
    confirm = input(f"\n⚠️ WARNING: You are about to delete {len(employees)} employees. This action cannot be undone!\nType 'DELETE' to confirm: ")
    
    if confirm != "DELETE":
        print("Deletion canceled.")
        return
    
    print(f"\nDeleting {len(employees)} employees...")
    deleted_count = 0
    
    for employee in employees:
        try:
            employee_id = employee["id"]
            print(f"Deleting employee {employee_id} ({employee['name']})...")
            
            response = requests.delete(f"{API_URL}/{employee_id}")
            
            if response.status_code == 200:
                result = response.json()
                if result["status"] == 200:
                    print(f"✅ Deleted employee: {employee_id}")
                    deleted_count += 1
                else:
                    print(f"❌ API error: {result['message']}")
            else:
                print(f"❌ HTTP error: {response.status_code}")
                
            # Add a small delay between requests
            time.sleep(0.5)
                
        except Exception as e:
            print(f"❌ Exception: {str(e)}")
    
    print(f"\nSuccessfully deleted {deleted_count} out of {len(employees)} employees")

def main():
    """Main function"""
    print("=" * 60)
    print("Enhanced Employee Data Generator".center(60))
    print("=" * 60)
    
    # Check for command line args
    if len(sys.argv) > 1 and sys.argv[1] == "--delete-all":
        delete_all_employees()
        return
    
    # First fetch existing employees
    existing_employees = fetch_existing_employees()
    
    # Ask user how many employees to create
    try:
        count = int(input("\nHow many employees would you like to create? (default: 5): ") or "5")
    except ValueError:
        count = 5
        print("Invalid input. Using default value of 5.")
    
    # Create employees
    created_employees = create_employees(count)
    
    # Save created employees to file
    if created_employees:
        filename = f"generated_employees_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(filename, "w") as f:
            json.dump(created_employees, f, indent=2)
        print(f"\nSaved created employees to {filename}")
    
    # Show final count
    print(f"\nTotal employees now in system: {len(existing_employees) + len(created_employees)}")
    print("\nDone!")

if __name__ == "__main__":
    main()