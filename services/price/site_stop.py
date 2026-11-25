from flask import request
from repository.price.stop_the_site import stop_the_site
from utils.log_response import _respond
from data.response import marshal_response_msg
from data.error_codes import BAD_REQUEST, INTERNAL_SERVER_ERROR, SUCCESS, INITIATING_FUNCTION


SOURCE = "/api/stop_site"

def response_log(custom_message, code, error, response_message=None):
    return _respond(
        body={},
        custom_message=custom_message,
        ipaddress=request.remote_addr,
        response_message=response_message,
        source="service",
        log_type="Site stop",
        message_code=f"PP{code}",
        log_status=code,
        error=error
    )

def site_stop():
    response_log("Entered in site stop function", INITIATING_FUNCTION, False)
    location_code = request.get_json()
    if not location_code:
        return marshal_response_msg({
            "error_message" : "Site IDs not found",
            "error_details" : "Site IDs is required, not founded",
            "error_code" : BAD_REQUEST,
            "is_error" : True
        })
    data, error = stop_the_site(location_code)
    if error['error']:
        return marshal_response_msg({
            "error_message" : "Site not stopped..",
            "error_details" : "Something went wrong, site is not stopped..",
            "error_code" : INTERNAL_SERVER_ERROR,
            "is_error" : True
        })
    response_log("Site stop function completed", SUCCESS, False)
    return marshal_response_msg({
        "success_message" : f"{data} sites stopped successfully",
        "success_code" : error['error_code'],
        "source" : SOURCE,
        "is_error" : False
    })