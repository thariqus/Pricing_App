from flask import request
from repository.price.get_all_site_data import get_all_site_data
from utils.log_response import _respond
from data.error_codes import INITIATING_FUNCTION, SUCCESS

def response_log(custom_message, code, error, response_message=None):
    return _respond(
        body={},
        custom_message=custom_message,
        ipaddress=request.remote_addr,
        response_message=response_message,
        source="service",
        log_type="Get all sites",
        message_code=f"PP{code}",
        log_status=code,
        error=error
    )

def get_all_sites():
    response_log("Entered in fetch all site function", INITIATING_FUNCTION, False)
    data = get_all_site_data()
    if data['response']['is_error']:
        return data
    response_log("Fetch all site function complete", SUCCESS, False)
    return data