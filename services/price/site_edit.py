import os
from flask import request
from repository.price.edit_one_site import edit_one_site
from data.response import marshal_response_msg
from data.error_codes import BAD_REQUEST, INITIATING_FUNCTION, SUCCESS, INTERNAL_SERVER_ERROR, UNAUTHORIZED
from utils.log_response import _respond

SOURCE = "/api/update_site/"
IS_CENTRAL = os.getenv("IS_CENTRAL")

def response_log(custom_message, code, error, response_message=None):
    return _respond(
        body={},
        custom_message=custom_message,
        ipaddress=request.remote_addr,
        response_message=response_message,
        source="service",
        log_type="Site edit",
        message_code=f"PP{code}",
        log_status=code,
        error=error
    )

def site_edit(site_id):
    response_log("Entered in site edit function", INITIATING_FUNCTION, False)
    if IS_CENTRAL != "1":
        return marshal_response_msg({
            "error_message" : "Permission Denided",
            "error_details" : "Request user is store and they have no permission to edit",
            "error_code" : UNAUTHORIZED,
            "is_error" : True
        })
    data = request.get_json()
    if not site_id:
        return marshal_response_msg({
            "error_message" : "Not found",
            "error_details" : "Site code is required",
            "error_code" : BAD_REQUEST,
            "is_error" : True
        })
    if not data:
        return marshal_response_msg({
            "error_message" : "Not found",
            "error_details" : "Request body is required",
            "error_code" : BAD_REQUEST,
            "is_error" : True
        })
    data, error = edit_one_site(site_id, data)
    if error['error']:
        return marshal_response_msg({
            "error_message" : "Data not edited..",
            "error_details" : "Something went wrong, Data is not edited..",
            "error_code" : INTERNAL_SERVER_ERROR,
            "is_error" : True
        })
    response_log("Site edit function completed", SUCCESS, False)
    return marshal_response_msg({
        "success_message" : f"{data} records deleted successfully",
        "success_code" : error['error_code'],
        "source" : SOURCE,
        "is_error" : False
    })