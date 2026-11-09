from flask import request
from services.price.ho_price_upload import ho_create_price
from data.response import marshal_response_msg
from data.error_codes import BAD_REQUEST, INITIATING_FUNCTION
from utils.log_response import _respond

def response_log(custom_message, code, error, response_message=None):
    return _respond(
        body={},
        custom_message=custom_message,
        ipaddress=request.remote_addr,
        response_message=response_message,
        source="service",
        log_type="HO to store csv",
        message_code=f"PP{code}",
        log_status=code,
        error=error
    )

def ho_to_store_csv():
    response_log("Entered in HO to store csv upload function", INITIATING_FUNCTION, False)
    data = request.get_json()
    if not data:
        response_log("Request body is empty, please provid a valid request body", BAD_REQUEST, True)
        return marshal_response_msg({
            "error_message" : "Not found",
            "error_details" : "Request body is empty, please provid a valid request body",
            "error_code" : BAD_REQUEST,
            "is_error" : True
        })
    response = ho_create_price(data, file=None, invalid_data=None)
    if response['response']['is_error']:
        return response
    return response