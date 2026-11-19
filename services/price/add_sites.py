import os
from flask import request
from repository.price.add_site_details import add_site_details
from utils.log_response import _respond
from data.error_codes import BAD_REQUEST, INITIATING_FUNCTION, SUCCESS, INTERNAL_SERVER_ERROR, UNAUTHORIZED
from data.response import marshal_response_msg

SOURCE = "/api/add_site_settings"
IS_CENTRAL = os.getenv("IS_CENTRAL")

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
    if IS_CENTRAL != "1":
        return marshal_response_msg({
            "error_message" : "Permission Denided",
            "error_details" : "Request user is store and they have no permission to edit",
            "error_code" : UNAUTHORIZED,
            "is_error" : True
        })
    data = request.get_json()
    if not data:
        response_log("Data is not found", BAD_REQUEST, True)
        return marshal_response_msg({
            "error_message" : "Data not found",
            "error_details" : "Data is required, but not found",
            "error_code" : BAD_REQUEST,
            "is_error" : True
        })
    data, error = add_site_details(data)
    if error['error']:
        response_log("Data not inserted", INTERNAL_SERVER_ERROR, True)
        return marshal_response_msg({
            "error_message" : "Data is not inserted",
            "error_details" : "Somethink went wrong, Data is not inserted",
            "error_code" : error['error_code'],
            "is_error" : True
        })
    response_log("Add site details completed", SUCCESS, False)
    message = ""
    if data['message_result']:
        message = f"{data['data']} records created successfully and site locations {data['message_result']} is already added.., please check it"
    else:
        message = f"{data['data']} records created successfully"
    return marshal_response_msg({
        "success_message" : message,
        "success_code" : error['error_code'],
        "source" : SOURCE,
        "is_error" : False
    })