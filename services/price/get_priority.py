from flask import request
from repository.price.get_price_priority import get_price_priority
from data.response import marshal_response_msg
from utils.log_response import _respond
from data.error_codes import INITIATING_FUNCTION, BAD_REQUEST, SUCCESS

SOURCE = "/api/get_discounted_item_price"

def response_log(custom_message, code, error, response_message=None):
    return _respond(
        body={},
        custom_message=custom_message,
        ipaddress=request.remote_addr,
        response_message=response_message,
        source="service",
        log_type="Get all priority",
        message_code=f"PP{code}",
        log_status=code,
        error=error
    )

def get_items_price_priority():
    response_log("Entered in fetch all price priority function", INITIATING_FUNCTION, False)
    data = request.get_json()
    if not data or not isinstance(data, dict):
        response_log("Request body is empty", BAD_REQUEST, False)
        return marshal_response_msg({
            "error_message" : "Not found",
            "error_details" : "Request body is empty, please provid a valid request body",
            "error_code" : BAD_REQUEST,
            "is_error" : True
        })
    data, error = get_price_priority(data)
    if error['error']:
        return marshal_response_msg({
            "error_message" : "No data founded",
            "error_details" : "Something went wrong, can't select item priority datas",
            "error_code" : error['error_code'],
            "is_error" : True
        })    
    response_log("Fetch all price priority function completed", SUCCESS, False)
    return marshal_response_msg({
        "data" : data,
        "success_message" : "Successfully selected item price priority",
        "success_code" : error['error_code'],
        "source" : SOURCE,
        "is_error" : False
    })