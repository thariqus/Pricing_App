from flask import request
from repository.price.update_price import update_price_data
from data.response import marshal_response_msg
from utils.log_response import _respond
from data.error_codes import INITIATING_FUNCTION, SUCCESS, BAD_REQUEST, INTERNAL_SERVER_ERROR
from utils.classes.price_body_validator import PriceConditionValidator



def response_log(custom_message, code, error, response_message=None):
    return _respond(
        body={},
        custom_message=custom_message,
        ipaddress=request.remote_addr,
        response_message=response_message,
        source="service",
        log_type="Update price",
        message_code=f"PP{code}",
        log_status=code,
        error=error
    )

def update_item_price():
    response_log("Entered in update price function", INITIATING_FUNCTION, False)
    data = request.get_json()
    if isinstance(data, dict):
                data = [data]
    if not isinstance(data, list):
        response_log("Request body must be an object or list of objects", BAD_REQUEST, True)
        return marshal_response_msg({
            "error_message" : "Not found",
            "error_details" : "Request body must be an object or list of objects",
            "error_code" : BAD_REQUEST,
            "is_error" : True
        })
    if not data:
        response_log("No update data received", BAD_REQUEST, True)
        return marshal_response_msg({
            "error_message" : "Not found",
            "error_details" : "No update data received",
            "error_code" : BAD_REQUEST,
            "is_error" : True
        })
    # try:
    #     data = PriceConditionValidator(data).validate()
    # except Exception as e:
    #     return marshal_response_msg({
    #         "error_message" : "Validation Error",
    #         "error_details" : str(e),
    #         "error_code" : INTERNAL_SERVER_ERROR,
    #         "is_error" : True,
    #     })
    mysql = update_price_data(data)
    if mysql['response']['is_error']:
        return mysql
    response_log("Update price function completed", SUCCESS, False)
    return mysql
        