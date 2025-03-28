from flask import Flask
from flask_restful import Api
from api.attendance_controller import AttendanceAPI, AttendanceByDateAPI, EmployeeAttendanceAPI, AttendanceLogsAPI, AppConfigAPI
from api.employee_status_api import EmployeeStatusAPI  # Import the new API
from api.attendance_summary_api import AttendanceSummaryAPI, AttendanceRangeAPI
from api.dashboard_api import DashboardAPI
from flask_cors import CORS
import os

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes
api = Api(app)

# API Routes
api.add_resource(AttendanceAPI, "/api/attendance")  # Clock-In/Out API
api.add_resource(AttendanceByDateAPI, "/api/attendance/date")  # Fetch records by date
api.add_resource(EmployeeAttendanceAPI, "/api/attendance/employee/<string:employee_id>")  # Fetch employee's attendance history
api.add_resource(AttendanceLogsAPI, "/api/attendance/logs")  # Fetch rejected attendance logs
api.add_resource(EmployeeStatusAPI, "/api/attendance/status")  # NEW: Get employee's current status

# Summary APIs
api.add_resource(AttendanceSummaryAPI, "/api/attendance/summary")  # Get attendance summary for a specific date
api.add_resource(AttendanceRangeAPI, "/api/attendance/range")  # Get attendance summary for a date range

# Dashboard API
api.add_resource(DashboardAPI, "/api/dashboard")  # Get dashboard data for cards and charts

# App Configuration API
api.add_resource(AppConfigAPI, "/api/config")  # Get and update application configuration

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5003))
    app.run(host="0.0.0.0", port=port, debug=True)