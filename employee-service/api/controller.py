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
        if not data:
            return response_wrapper(400, "Invalid JSON or no data provided", None)
            
        result = add_employee(data)
        # add_employee already returns the response_wrapper tuple
        return result
        
    except Exception as e:
        error_message = f"Error in create_employee: {str(e)}"
        print(error_message)
        return response_wrapper(500, error_message, None)


@employee_blueprint.route("/login", methods=["POST"])
def login():
    """Employee login"""
    try:
        data = request.get_json()
        if not data:
            return response_wrapper(400, "Invalid JSON or no data provided", None)
            
        # login_employee already returns the response_wrapper tuple
        return login_employee(data)
        
    except Exception as e:
        error_message = f"Error in login: {str(e)}"
        print(error_message)
        return response_wrapper(500, error_message, None)


@employee_blueprint.route("/<employee_id>", methods=["GET"])
def fetch_employee(employee_id):
    """Fetch a single employee by ID"""
    try:
        # get_employee already returns the response_wrapper tuple
        return get_employee(employee_id)
        
    except Exception as e:
        error_message = f"Error in fetch_employee: {str(e)}"
        print(error_message)
        return response_wrapper(500, error_message, None)


@employee_blueprint.route("/<employee_id>", methods=["PUT"])
def update_employee_route(employee_id):
    """Update an employee's information, including password management"""
    try:
        data = request.get_json()
        if not data:
            return response_wrapper(400, "Invalid JSON or no data provided", None)
            
        # update_employee already returns the response_wrapper tuple
        return update_employee(employee_id, data)
        
    except Exception as e:
        error_message = f"Error in update_employee_route: {str(e)}"
        print(error_message)
        return response_wrapper(500, error_message, None)


@employee_blueprint.route("/<employee_id>/reset-password", methods=["POST"])
def reset_employee_password(employee_id):
    """Reset an employee's password"""
    try:
        # Create update data with only the password reset flag
        data = {"update_password": True}
        
        # update_employee already returns the response_wrapper tuple
        return update_employee(employee_id, data)
        
    except Exception as e:
        error_message = f"Error in reset_employee_password: {str(e)}"
        print(error_message)
        return response_wrapper(500, error_message, None)


@employee_blueprint.route("/<employee_id>", methods=["DELETE"])
def delete_employee_route(employee_id):
    """Delete an employee"""
    try:
        # delete_employee already returns the response_wrapper tuple
        return delete_employee(employee_id)
        
    except Exception as e:
        error_message = f"Error in delete_employee_route: {str(e)}"
        print(error_message)
        return response_wrapper(500, error_message, None)


@employee_blueprint.route("/all", methods=["GET"])
def fetch_all_employees():
    """Fetch all employees"""
    try:
        # get_all_employees already returns the response_wrapper tuple
        return get_all_employees()
        
    except Exception as e:
        error_message = f"Error in fetch_all_employees: {str(e)}"
        print(error_message)
        return response_wrapper(500, error_message, None)


@employee_blueprint.route("/verify", methods=["GET"])
def check_employee_exists():
    """Verify if an employee exists"""
    try:
        employee_id = request.args.get("id")
        if not employee_id:
            return response_wrapper(400, "Employee ID is required", None)

        # verify_employee_exists already returns the response_wrapper tuple
        return verify_employee_exists(employee_id)
        
    except Exception as e:
        error_message = f"Error in check_employee_exists: {str(e)}"
        print(error_message)
        return response_wrapper(500, error_message, None)


@employee_blueprint.route("/search", methods=["GET"])
def search_employees():
    """Search for employees by name, email, or designation"""
    try:
        query = request.args.get("q", "")
        field = request.args.get("field", "name")  # Default search by name
        
        if not query:
            return response_wrapper(400, "Search query is required", None)
        
        # get_all_employees already returns the response_wrapper tuple
        employees_response = get_all_employees()
        
        # Since employees_response is already a tuple (jsonify(response), status_code)
        # we need to extract the data from it
        response_json = employees_response[0].json
        
        if response_json["status"] != 200:
            # If there was an error, just return the original response
            return employees_response
            
        # Filter employees by search criteria
        employees_list = response_json["data"]
        if not employees_list:
            employees_list = []
            
        filtered_employees = []
        for employee in employees_list:
            if field in employee and query.lower() in str(employee[field]).lower():
                filtered_employees.append(employee)
        
        return response_wrapper(200, f"Found {len(filtered_employees)} matching employees", filtered_employees)
        
    except Exception as e:
        error_message = f"Error in search_employees: {str(e)}"
        print(error_message)
        return response_wrapper(500, error_message, None)


@employee_blueprint.route("/department/<department>", methods=["GET"])
def get_employees_by_department(department):
    """Get employees by department"""
    try:
        # get_all_employees already returns the response_wrapper tuple
        employees_response = get_all_employees()
        
        # Since employees_response is already a tuple (jsonify(response), status_code)
        # we need to extract the data from it
        response_json = employees_response[0].json
        
        if response_json["status"] != 200:
            # If there was an error, just return the original response
            return employees_response
            
        # Filter employees by department
        employees_list = response_json["data"]
        if not employees_list:
            employees_list = []
            
        filtered_employees = []
        for employee in employees_list:
            if "designation" in employee and department.lower() in employee["designation"].lower():
                filtered_employees.append(employee)
        
        return response_wrapper(200, f"Found {len(filtered_employees)} employees in {department}", filtered_employees)
        
    except Exception as e:
        error_message = f"Error in get_employees_by_department: {str(e)}"
        print(error_message)
        return response_wrapper(500, error_message, None)


@employee_blueprint.route("/designation/<designation>", methods=["GET"])
def get_employees_by_designation_route(designation):
    """Get employees by exact designation/role"""
    try:
        # get_employees_by_designation already returns the response_wrapper tuple
        return get_employees_by_designation(designation)
        
    except Exception as e:
        error_message = f"Error in get_employees_by_designation_route: {str(e)}"
        print(error_message)
        return response_wrapper(500, error_message, None)