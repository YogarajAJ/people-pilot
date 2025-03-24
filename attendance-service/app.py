from flask import Flask
from flask_restful import Api
from api.attendance_controller import AttendanceAPI, AttendanceByDateAPI, EmployeeAttendanceAPI
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

# Summary APIs
api.add_resource(AttendanceSummaryAPI, "/api/attendance/summary")  # Get attendance summary for a specific date
api.add_resource(AttendanceRangeAPI, "/api/attendance/range")  # Get attendance summary for a date range

# Dashboard API
api.add_resource(DashboardAPI, "/api/dashboard")  # Get dashboard data for cards and charts

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5003))
    app.run(host="0.0.0.0", port=port, debug=True)