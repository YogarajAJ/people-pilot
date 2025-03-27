import bcrypt
import string
import random
from datetime import datetime
from firestore import FirestoreDB
from utils.response_wrapper import response_wrapper

db = FirestoreDB()
EMPLOYEE_COLLECTION = "employees"


def generate_unique_password(length=12):
    """Generate a unique, secure password"""
    # Define character sets for password
    lowercase = string.ascii_lowercase
    uppercase = string.ascii_uppercase
    digits = string.digits
    special_chars = "!@#$%^&*()_-+=<>?"
    
    # Ensure password has at least one character from each set
    password = [
        random.choice(lowercase),
        random.choice(uppercase),
        random.choice(digits),
        random.choice(special_chars)
    ]
    
    # Fill the rest of the password
    all_chars = lowercase + uppercase + digits + special_chars
    password.extend(random.choice(all_chars) for _ in range(length - 4))
    
    # Shuffle the password characters
    random.shuffle(password)
    
    # Convert list to string
    return ''.join(password)


def get_next_employee_id():
    """Fetch the next sequential employee ID"""
    employees = db.get_all_documents(EMPLOYEE_COLLECTION)
    
    if not employees:
        return "EMP001"  # Start with EMP001 if no employees exist
    
    # Extract numeric part from EMP*** format and find the max
    emp_numbers = []
    for emp in employees:
        if "id" in emp and emp["id"].startswith("EMP"):
            try:
                num = int(emp["id"][3:])  # Extract the number after "EMP"
                emp_numbers.append(num)
            except ValueError:
                # Skip if not in the expected format
                continue
    
    if not emp_numbers:
        return "EMP001"  # Start with EMP001 if no valid IDs found
        
    next_number = max(emp_numbers) + 1
    return f"EMP{next_number:03d}"  # Format as EMP001, EMP002, etc.


def add_employee(data):
    """Register a new employee with auto-generated password"""
    required_fields = ["name", "age", "date_of_birth", "email", "address", "blood_type",
                       "phone_number", "designation", "ctc", "employee_shift_hours"]

    if not data or any(k not in data or data[k] in [None, ""] for k in required_fields):
        return response_wrapper(400, "Missing required fields", None)

    email = data["email"]

    # Check if employee already exists with this email
    existing_employees = db.get_documents_by_field(EMPLOYEE_COLLECTION, "email", email)
    if existing_employees:
        return response_wrapper(400, "Employee with this email already exists", None)

    # Generate a unique employee ID
    employee_id = get_next_employee_id()
    
    # Generate a unique password
    raw_password = generate_unique_password()
    
    # Hash the password before storing
    hashed_password = bcrypt.hashpw(raw_password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

    employee_data = {
        "id": employee_id,
        "name": data["name"],
        "age": data["age"],
        "date_of_birth": data["date_of_birth"],
        "email": email,
        "address": data["address"],
        "blood_type": data["blood_type"],
        "phone_number": data["phone_number"],
        "designation": data["designation"],
        "ctc": data["ctc"],
        "password": hashed_password,  # Store hashed password
        "employee_shift_hours": data["employee_shift_hours"],
        "created_at": datetime.utcnow().isoformat(),
        "last_login": None
    }

    # Add the document with employee_id as the document ID
    db.add_document(EMPLOYEE_COLLECTION, employee_id, employee_data)
    
    # Return the employee data with the raw password for first-time use
    response_data = employee_data.copy()
    response_data["raw_password"] = raw_password  # Include raw password in response only
    return response_wrapper(201, "Employee registered successfully with auto-generated password", response_data)


def update_employee(employee_id, data):
    """Update an existing employee"""
    if not employee_id:
        return response_wrapper(400, "Employee ID is required", None)
        
    # Check if employee exists
    existing_employee = db.get_document(EMPLOYEE_COLLECTION, employee_id)
    if not existing_employee:
        return response_wrapper(404, "Employee not found", None)
        
    # Check if email is being updated and is already in use by another employee
    if "email" in data and data["email"] != existing_employee["email"]:
        existing_emails = db.get_documents_by_field(EMPLOYEE_COLLECTION, "email", data["email"])
        for emp in existing_emails:
            if emp["id"] != employee_id:  # If email belongs to a different employee
                return response_wrapper(400, "Email already in use by another employee", None)
    
    # Create a copy of the data for the response
    response_data = {}
            
    # Handle password update
    if "update_password" in data and data["update_password"] is True:
        # Generate a new password if requested
        raw_password = generate_unique_password()
        hashed_password = bcrypt.hashpw(raw_password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
        data["password"] = hashed_password
        # Remove update_password flag as it's not needed in the database
        del data["update_password"]
        # Add the raw password to the response
        response_data["raw_password"] = raw_password
    elif "password" in data:
        # If a specific password is provided, hash it
        if data["password"]:
            data["password"] = bcrypt.hashpw(data["password"].encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
        else:
            # If empty password is provided, remove it from the update
            del data["password"]
        
    # Add last updated timestamp
    data["updated_at"] = datetime.utcnow().isoformat()
    
    # Update employee data
    db.update_document(EMPLOYEE_COLLECTION, employee_id, data)
    
    # Fetch updated employee data
    updated_employee = db.get_document(EMPLOYEE_COLLECTION, employee_id)
    
    # Merge the updated employee with any response data (like raw password)
    response_data.update(updated_employee)
    
    return response_wrapper(200, "Employee updated successfully", response_data)


def login_employee(data):
    """Authenticate employee (Login)"""
    required_fields = ["email", "password"]

    if not data or not all(k in data for k in required_fields):
        return response_wrapper(400, "Email and password are required", None)

    email = data["email"]
    password = data["password"]

    # Fetch employee from Firestore by email
    employees = db.get_documents_by_field(EMPLOYEE_COLLECTION, "email", email)
    if not employees:
        return response_wrapper(401, "Invalid email or password", None)
    
    employee = employees[0]  # Use the first match (should be only one)
    stored_password = employee.get("password")

    # Verify password
    if not bcrypt.checkpw(password.encode("utf-8"), stored_password.encode("utf-8")):
        return response_wrapper(401, "Invalid email or password", None)

    # Update last login time
    db.update_document(EMPLOYEE_COLLECTION, employee["id"], {"last_login": datetime.utcnow().isoformat()})

    return response_wrapper(200, "Login successful", employee)


def get_employee(employee_id):
    """Fetch employee by ID"""
    if not employee_id:
        return response_wrapper(400, "Employee ID is required", None)

    employee = db.get_document(EMPLOYEE_COLLECTION, employee_id)
    if not employee:
        return response_wrapper(404, "Employee not found", None)

    return response_wrapper(200, "Employee details fetched", employee)


def get_all_employees():
    """Fetch all employees"""
    employees = db.get_all_documents(EMPLOYEE_COLLECTION)
    return response_wrapper(200, "All employees fetched", employees)


def verify_employee_exists(employee_id):
    """Check if an employee exists"""
    employee = db.get_document(EMPLOYEE_COLLECTION, employee_id)
    return response_wrapper(200, "Employee exists" if employee else "Employee does not exist",
                            {"exists": bool(employee)})


def get_employees_by_designation(designation):
    """Get employees by designation/role"""
    if not designation:
        return response_wrapper(400, "Designation is required", None)
        
    employees = db.get_all_documents(EMPLOYEE_COLLECTION)
    filtered_employees = [emp for emp in employees if emp.get("designation", "").lower() == designation.lower()]
    
    return response_wrapper(200, f"Found {len(filtered_employees)} employees with designation '{designation}'", 
                           filtered_employees)


def delete_employee(employee_id):
    """Delete an employee"""
    if not employee_id:
        return response_wrapper(400, "Employee ID is required", None)
        
    # Check if employee exists
    employee = db.get_document(EMPLOYEE_COLLECTION, employee_id)
    if not employee:
        return response_wrapper(404, "Employee not found", None)
        
    # Delete the employee
    db.delete_document(EMPLOYEE_COLLECTION, employee_id)
    
    return response_wrapper(200, "Employee deleted successfully", {"id": employee_id})