def response_wrapper(status, message, data):
    return {"status": status, "message": message, "data": data}, status
