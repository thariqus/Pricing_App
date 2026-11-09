from flask import request
from repository.price.add_site_details import add_site_details
from utils.log_response import _respond
from data.error_codes import BAD_REQUEST, INITIATING_FUNCTION, SUCCESS
from data.response import marshal_response_msg

def response_log(custom_message, code, error, response_message=None):
    return _respond(
        body={},
        custom_message=custom_message,
        ipaddress=request.remote_addr,
        response_message=response_message,
        source="service",
        log_type="Add site details",
        message_code=f"PP{code}",
        log_status=code,
        error=error
    )

def add_sites():
    response_log("Entered in add site details function", INITIATING_FUNCTION, False)
    data = request.get_json()
    if not data:
        response_log("Data is not found", BAD_REQUEST, True)
        return marshal_response_msg({
            "error_message" : "Not found",
            "error_details" : "Data is required, but not found",
            "error_code" : BAD_REQUEST,
            "is_error" : True
        })
    data = add_site_details(data)
    if data['response']['is_error']:
        return data
    response_log("Add site details completed", SUCCESS, False)
    return data