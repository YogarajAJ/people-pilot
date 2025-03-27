from flask import Blueprint, request, jsonify
from api.service import (
    add_employee, 
    login_employee, 
    get_employee, 
    get_all_employees, 
    verify_employee_exists,
    update_employee,
    get_employees_by_designation,
    delete_employee
)
from utils.response_wrapper import response_wrapper

employee_blueprint = Blueprint("employee", __name__)


@employee_blueprint.route("/register", methods=["POST"])
def create_employee():
    """Create a new employee with auto-generated password"""
    try:
        data = request.get_json()
        result = add_employee(data)
        
        # If successful, log the auto-generated password but don't store it
        if result.get("status") == 201 and "raw_password" in result.get("data", {}):
            print(f"Auto-generated password for {result['data'].get('email')}: {result['data']['raw_password']}")
            
            # You may want to send the password via email here
            # send_welcome_email(result['data']['email'], result['data']['raw_password'])
            
            # Remove the raw password from the response data before sending to client
            # (optional - you might want to keep it for first-time login purposes)
            # del result['data']['raw_password']
        
        return result
    except Exception as e:
        return response_wrapper(500, str(e), None)


@employee_blueprint.route("/login", methods=["POST"])
def login():
    """Employee login"""
    try:
        data = request.get_json()
        return login_employee(data)
    except Exception as e:
        return response_wrapper(500, str(e), None)


@employee_blueprint.route("/<employee_id>", methods=["GET"])
def fetch_employee(employee_id):
    """Fetch a single employee by ID"""
    try:
        return get_employee(employee_id)
    except Exception as e:
        return response_wrapper(500, str(e), None)


@employee_blueprint.route("/<employee_id>", methods=["PUT"])
def update_employee_route(employee_id):
    """Update an employee's information, including password management"""
    try:
        data = request.get_json()
        result = update_employee(employee_id, data)
        
        # If successful and a new password was generated
        if result.get("status") == 200 and "raw_password" in result.get("data", {}):
            print(f"New password for employee {employee_id}: {result['data']['raw_password']}")
            
            # You may want to send the password via email here
            # send_password_update_email(result['data']['email'], result['data']['raw_password'])
            
            # Remove the raw password from the response data before sending to client
            # (optional - you might want to keep it for first-time login purposes)
            # del result['data']['raw_password']
        
        return result
    except Exception as e:
        return response_wrapper(500, str(e), None)


@employee_blueprint.route("/<employee_id>/reset-password", methods=["POST"])
def reset_employee_password(employee_id):
    """Reset an employee's password"""
    try:
        # Create update data with only the password reset flag
        data = {"update_password": True}
        result = update_employee(employee_id, data)
        
        # Handle the result as in the update route
        if result.get("status") == 200 and "raw_password" in result.get("data", {}):
            print(f"Password reset for employee {employee_id}: {result['data']['raw_password']}")
            
            # You may want to send the password via email here
            # send_password_reset_email(result['data']['email'], result['data']['raw_password'])
        
        return result
    except Exception as e:
        return response_wrapper(500, str(e), None)


@employee_blueprint.route("/<employee_id>", methods=["DELETE"])
def delete_employee_route(employee_id):
    """Delete an employee"""
    try:
        return delete_employee(employee_id)
    except Exception as e:
        return response_wrapper(500, str(e), None)


@employee_blueprint.route("/all", methods=["GET"])
def fetch_all_employees():
    """Fetch all employees"""
    try:
        return get_all_employees()
    except Exception as e:
        return response_wrapper(500, str(e), None)


@employee_blueprint.route("/verify", methods=["GET"])
def check_employee_exists():
    """Verify if an employee exists"""
    try:
        employee_id = request.args.get("id")
        if not employee_id:
            return response_wrapper(400, "Employee ID is required", None)

        return verify_employee_exists(employee_id)
    except Exception as e:
        return response_wrapper(500, str(e), None)


@employee_blueprint.route("/search", methods=["GET"])
def search_employees():
    """Search for employees by name, email, or designation"""
    try:
        query = request.args.get("q", "")
        field = request.args.get("field", "name")  # Default search by name
        
        if not query:
            return response_wrapper(400, "Search query is required", None)
        
        employees = get_all_employees()
        
        # Filter from the response data
        if employees.get("status") == 200:
            filtered_employees = []
            for employee in employees.get("data", []):
                if field in employee and query.lower() in str(employee[field]).lower():
                    filtered_employees.append(employee)
            
            return response_wrapper(200, f"Found {len(filtered_employees)} matching employees", filtered_employees)
        else:
            return employees  # Return the error response as is
    except Exception as e:
        return response_wrapper(500, str(e), None)


@employee_blueprint.route("/department/<department>", methods=["GET"])
def get_employees_by_department(department):
    """Get employees by department"""
    try:
        employees = get_all_employees()
        
        # Filter from the response data
        if employees.get("status") == 200:
            filtered_employees = []
            for employee in employees.get("data", []):
                if "designation" in employee and department.lower() in employee["designation"].lower():
                    filtered_employees.append(employee)
            
            return response_wrapper(200, f"Found {len(filtered_employees)} employees in {department}", filtered_employees)
        else:
            return employees  # Return the error response as is
    except Exception as e:
        return response_wrapper(500, str(e), None)


@employee_blueprint.route("/designation/<designation>", methods=["GET"])
def get_employees_by_designation_route(designation):
    """Get employees by exact designation/role"""
    try:
        return get_employees_by_designation(designation)
    except Exception as e:
        return response_wrapper(500, str(e), None)