from flask import request
from repository.price.get_log_messages import get_log_messages
from utils.log_response import _respond
from data.error_codes import INITIATING_FUNCTION, SUCCESS

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
    data = get_log_messages()
    if data['response']['is_error']:
        return data
    response_log("Fetch all log message function completed", SUCCESS, False)
    return data['response']['data']