from flask import request
from repository.price.get_all_site_data import get_all_site_data
from utils.log_response import _respond
from data.error_codes import INITIATING_FUNCTION, SUCCESS
from data.response import marshal_response_msg

SOURCE = "/api/get_all_sites"

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
    data, error = get_all_site_data()
    if error['error']:
        return marshal_response_msg({
            "error_message" : "No data founded",
            "error_details" : "Something went wrong, can't select site datas",
            "error_code" : error['error_code'],
            "is_error" : True
        })
    response_log("Fetch all site function complete", SUCCESS, False)
    return marshal_response_msg({
        "data" : data,
        "success_message" : "Successfully selected item datas",
        "success_code" : error['error_code'],
        "source" : SOURCE,
        "is_error" : False
    })