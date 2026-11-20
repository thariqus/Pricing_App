from flask import request
from repository.price.get_log_messages import get_log_messages
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
        log_type="Get all log messages",
        message_code=f"PP{code}",
        log_status=code,
        error=error
    )

def get_logs():
    response_log("Entered in fetch all log message function", INITIATING_FUNCTION, False)
    data, error = get_log_messages()
    if error['error']:
        return marshal_response_msg({
            "error_message" : "No data founded",
            "error_details" : "Something went wrong, can't select log message datas",
            "error_code" : error['error_code'],
            "is_error" : True,
            "custom_field" : {
                "page" : error['page'],
                "limit" : error['limit']
            }
        })
    response_log("Fetch all log message function completed", SUCCESS, False)
    return marshal_response_msg({
        "data" : data['data'],
        "success_message" : "Successfully selected log message",
        "success_code" : error['error_code'],
        "is_error" : False,
        "custom_field" : {
            "page" : data['page'],
            "limit" : data['limit']
        }
    })