from flask import Flask
from flask_restful import Api
from api.employee_controller import EmployeeAPI, EmployeeListAPI

app = Flask(__name__)
api = Api(app)

# Define routes
api.add_resource(EmployeeAPI, "/api/employee")  # Single Employee (Add & Get)
api.add_resource(EmployeeListAPI, "/api/employee/list")  # Single Employee (Add & Get)


if __name__ == "__main__":
    app.run(debug=True, port=5001)  # Run Employee microservice on port 5001
