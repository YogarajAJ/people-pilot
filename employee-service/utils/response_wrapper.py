from flask import jsonify

def response_wrapper(status_code, message, data):
    """
    Standardized response format for all API endpoints
    
    Args:
        status_code (int): HTTP status code
        message (str): Response message
        data (any): Response data, can be None
        
    Returns:
        JSON response with status, message and data fields
    """
    response = {
        "status": status_code,
        "message": message,
        "data": data
    }
    
    return jsonify(response), status_code