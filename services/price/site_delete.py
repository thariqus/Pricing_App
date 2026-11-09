from flask import request
from repository.price.delete_one_site import delete_one_site
from data.response import marshal_response_msg
from data.error_codes import BAD_REQUEST, INITIATING_FUNCTION, SUCCESS
from utils.log_response import _respond

def response_log(custom_message, code, error, response_message=None):
    return _respond(
        body={},
        custom_message=custom_message,
        ipaddress=request.remote_addr,
        response_message=response_message,
        source="service",
        log_type="Site delete",
        message_code=f"PP{code}",
        log_status=code,
        error=error
    )

def site_delete(site_id):
    response_log("Entered in site delete function", INITIATING_FUNCTION, False)
    if not site_id:
        return marshal_response_msg({
            "error_message" : "Not found",
            "error_details" : "Site code is required",
            "error_code" : BAD_REQUEST,
            "is_error" : True
        })
    data = delete_one_site(site_id)
    if data['response']['is_error']:
        return data
    response_log("Site delete function completed", SUCCESS, False)
    return data