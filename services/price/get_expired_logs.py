from flask import request
from repository.price.fetch_expired_logs import fetch_expired_logs 
from utils.log_response import _respond
from data.error_codes import INITIATING_FUNCTION, SUCCESS
from data.response import marshal_response_msg

def response_log(custom_message, code, error, response_message=None):
    return _respond(
        body={},
        custom_message=custom_message,
        ipaddress=request.remote_addr,
        response_message=response_message,
        source="service",
        log_type="Get all expired log messages",
        message_code=f"PP{code}",
        log_status=code,
        error=error
    )

def get_expired_logs():
    response_log("Entered in fetch all expired log message function", INITIATING_FUNCTION, False)
    data, error = fetch_expired_logs()
    if error['error']:
        return marshal_response_msg({
            "error_message" : "No data founded, can't select all expired log message datas",
            "error_details" : "Something went wrong, can't select all expired log message datas",
            "error_code" : error['error_code'],
            "is_error" : True,
            "custom_field" : {
                "page" : error['page'],
                "limit" : error['limit']
            }
        })
    response_log("Fetch all expired log message function completed", SUCCESS, False)
    return marshal_response_msg({
        "data" : data['data'],
        "success_message" : "Successfully selected expired log message",
        "success_code" : error['error_code'],
        "is_error" : False,
        "custom_field" : {
            "page" : data['page'],
            "limit" : data['limit']
        }
    })