from flask import Blueprint, request
from api.service import add_employee, get_employee, get_all_employees, verify_employee_exists
from utils.response_wrapper import response_wrapper

employee_blueprint = Blueprint("employee", __name__)


@employee_blueprint.route("", methods=["POST"])
def create_employee():
    """Create a new employee"""
    try:
        data = request.get_json()
        return add_employee(data)
    except Exception as e:
        return response_wrapper(500, str(e), None)


@employee_blueprint.route("", methods=["GET"])
def fetch_employee():
    """Fetch a single employee"""
    try:
        employee_id = request.args.get("id")
        return get_employee(employee_id)
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

        exists = verify_employee_exists(employee_id)
        return response_wrapper(200, "Employee exists" if exists else "Employee does not exist", {"exists": exists})

    except Exception as e:
        return response_wrapper(500, str(e), None)
