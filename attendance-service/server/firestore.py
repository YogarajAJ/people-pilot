from config import db
from datetime import datetime, timedelta

class FirestoreDB:
    def __init__(self):
        self.collection = db.collection("attendance")

    def add_record(self, data):
        """Add attendance record."""
        self.collection.document(data["id"]).set(data)
        return True

    def get_records(self, employee_id):
        """Fetch records by employee ID."""
        docs = self.collection.where("employee_id", "==", employee_id).stream()
        return [doc.to_dict() for doc in docs]

    def get_records_by_date(self, employee_id, date_str):
        """Fetch attendance records by date for a specific employee."""
        docs = self.collection.where("employee_id", "==", employee_id).where("date", "==", date_str).stream()
        return [doc.to_dict() for doc in docs]
    
    def get_all_records_by_date(self, date_str):
        """Fetch all attendance records for a specific date."""
        docs = self.collection.where("date", "==", date_str).stream()
        return [doc.to_dict() for doc in docs]
    
    def get_employee_attendance_history(self, employee_id, start_date=None, end_date=None):
        """
        Fetch attendance history for a specific employee with optional date range filtering.
        
        Args:
            employee_id (str): The employee ID
            start_date (str, optional): Start date in ISO format (YYYY-MM-DD)
            end_date (str, optional): End date in ISO format (YYYY-MM-DD)
        """
        query = self.collection.where("employee_id", "==", employee_id)
        
        # Firestore can only use one range operator per query
        # So we'll apply the date filter after fetching
        docs = query.stream()
        records = [doc.to_dict() for doc in docs]
        
        # Apply date filtering after getting the records
        filtered_records = []
        for record in records:
            date = record.get("date")
            if not date:
                continue
                
            include = True
            if start_date and date < start_date:
                include = False
            if end_date and date > end_date:
                include = False
                
            if include:
                filtered_records.append(record)
                
        return filtered_records
    
    def get_records_by_date_range(self, start_date, end_date=None):
        """
        Fetch all attendance records within a date range.
        
        Args:
            start_date (str): Start date in ISO format (YYYY-MM-DD)
            end_date (str, optional): End date in ISO format (YYYY-MM-DD), defaults to today
        """
        if not end_date:
            end_date = datetime.utcnow().date().isoformat()
        
        # Firestore can handle range queries on a single field
        query = self.collection.where("date", ">=", start_date).where("date", "<=", end_date)
        docs = query.stream()
        return [doc.to_dict() for doc in docs]
    
    def get_attendance_stats_by_date(self, date_str):
        """
        Get attendance statistics for a specific date.
        
        Args:
            date_str (str): Date in ISO format (YYYY-MM-DD)
            
        Returns:
            dict: Dictionary containing attendance statistics
        """
        records = self.get_all_records_by_date(date_str)
        
        # Get unique employee IDs (present employees)
        present_employee_ids = set()
        valid_location_count = 0
        invalid_location_count = 0
        
        for record in records:
            employee_id = record.get("employee_id")
            status = record.get("status")
            
            if employee_id:
                present_employee_ids.add(employee_id)
                
            if status == "VALID":
                valid_location_count += 1
            elif status == "INVALID_LOCATION":
                invalid_location_count += 1
        
        present_count = len(present_employee_ids)
        
        return {
            "date": date_str,
            "present_count": present_count,
            "within_office_count": valid_location_count,
            "outside_office_count": invalid_location_count,
            "present_employee_ids": list(present_employee_ids)
        }
    
    def get_employee_attendance_count(self, employee_id, start_date=None, end_date=None):
        """
        Get attendance count for a specific employee in a date range.
        
        Args:
            employee_id (str): The employee ID
            start_date (str, optional): Start date in ISO format (YYYY-MM-DD)
            end_date (str, optional): End date in ISO format (YYYY-MM-DD)
            
        Returns:
            dict: Dictionary containing attendance counts
        """
        records = self.get_employee_attendance_history(employee_id, start_date, end_date)
        
        total_days = len(records)
        valid_days = sum(1 for r in records if r.get("status") == "VALID")
        invalid_days = total_days - valid_days
        
        return {
            "employee_id": employee_id,
            "total_days": total_days,
            "valid_days": valid_days,
            "invalid_days": invalid_days,
            "start_date": start_date,
            "end_date": end_date
        }