from flask import Flask
from flask_restful import Api
from api.attendance_controller import AttendanceAPI

app = Flask(__name__)
api = Api(app)

# Define API routes
api.add_resource(AttendanceAPI, "/api/attendance")

if __name__ == "__main__":
    app.run(debug=True,port=5002)
