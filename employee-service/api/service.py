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
        return 10000  # Start from 10000 if no employees exist
    max_id = max(int(emp["id"]) for emp in employees if "id" in emp)
    return max_id + 1


def add_employee(data):
    """Register a new employee with password encryption"""
    """employe shift hours"""
    required_fields = ["name", "age", "date_of_birth", "email", "address", "blood_type",
                       "phone_number", "designation", "ctc", "password","employee_shift_hours"]

    # if not data or not all(k in data for k in required_fields):
    #     return response_wrapper(400, "Missing required fields", None)
    if not data or any(k not in data or data[k] in [None, ""] for k in required_fields):
        return response_wrapper(400, "Missing required fields", None)


    email = data["email"]

    # Check if employee already exists
    existing_employee = db.get_document_by_field(EMPLOYEE_COLLECTION, "email", email)
    if existing_employee:
        return response_wrapper(400, "Employee with this email already exists", None)

    employee_id = str(get_next_employee_id())  # Generate sequential ID

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

    db.add_document(EMPLOYEE_COLLECTION, employee_id, employee_data)
    return response_wrapper(201, "Employee registered successfully", employee_data)


def login_employee(data):
    """Authenticate employee (Login)"""
    required_fields = ["email", "password"]

    if not data or not all(k in data for k in required_fields):
        return response_wrapper(400, "Email and password are required", None)

    email = data["email"]
    password = data["password"]

    # Fetch employee from Firestore
    employee = db.get_document_by_field(EMPLOYEE_COLLECTION, "email", email)
    if not employee:
        return response_wrapper(401, "Invalid email or password", None)

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
