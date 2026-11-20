from flask import request
from repository.price.create_single_price import create_single_price
from data.response import marshal_response_msg
from data.error_codes import BAD_REQUEST, INITIATING_FUNCTION, SUCCESS, INTERNAL_SERVER_ERROR
from utils.log_response import _respond

SOURCE = "/api/items/create_singel_item_price"

def response_log(custom_message, code, error, response_message=None):
    return _respond(
        body={},
        custom_message=custom_message,
        ipaddress=request.remote_addr,
        response_message=response_message,
        source="service",
        log_type="HO to store single price integration",
        message_code=f"PP{code}",
        log_status=code,
        error=error
    )

def ho_to_store_single_price():
    response_log("Entered in HO to store singel price integration function", INITIATING_FUNCTION, False)
    data = request.get_json()
    if not data:
        return marshal_response_msg({
            "error_message" : "Not found",
            "error_details" : "Request body is empty, please provid a valid request body",
            "error_code" : BAD_REQUEST,
            "is_error" : True
        })
    data, error = create_single_price(data)
    if error['error']:
        return marshal_response_msg({
            "error_message" : "Data not inserted",
            "error_details" : "Something went wrong, can't insert the current item",
            "error_code" : INTERNAL_SERVER_ERROR,
            "is_error" : True
        })
    response_log("HO to store singel price integration function completed", SUCCESS, False)
    return marshal_response_msg({
        "success_message" : f"{data} records created successfully",
        "success_code" : error['error_code'],
        "source" : SOURCE,
        "is_error" : False
    })