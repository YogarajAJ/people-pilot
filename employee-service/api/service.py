import bcrypt
from datetime import datetime
from firestore import FirestoreDB
from utils.response_wrapper import response_wrapper

db = FirestoreDB()
EMPLOYEE_COLLECTION = "employees"


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
    """Register a new employee with password encryption"""
    required_fields = ["name", "age", "date_of_birth", "email", "address", "blood_type",
                       "phone_number", "designation", "ctc", "password", "employee_shift_hours"]

    if not data or any(k not in data or data[k] in [None, ""] for k in required_fields):
        return response_wrapper(400, "Missing required fields", None)

    email = data["email"]

    # Check if employee already exists with this email
    existing_employees = db.get_documents_by_field(EMPLOYEE_COLLECTION, "email", email)
    if existing_employees:
        return response_wrapper(400, "Employee with this email already exists", None)

    # Generate a unique employee ID
    employee_id = get_next_employee_id()

    # Hash the password before storing
    hashed_password = bcrypt.hashpw(data["password"].encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

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
    return response_wrapper(201, "Employee registered successfully", employee_data)


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
            
    # Hash password if provided
    if "password" in data and data["password"]:
        data["password"] = bcrypt.hashpw(data["password"].encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
        
    # Add last updated timestamp
    data["updated_at"] = datetime.utcnow().isoformat()
    
    # Update employee data
    db.update_document(EMPLOYEE_COLLECTION, employee_id, data)
    
    # Fetch and return updated employee data
    updated_employee = db.get_document(EMPLOYEE_COLLECTION, employee_id)
    return response_wrapper(200, "Employee updated successfully", updated_employee)


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