from flask import request
from repository.price.filter_price_data import filter_price_data
from data.response import marshal_response_msg
from utils.log_response import _respond
from data.error_codes import INITIATING_FUNCTION, BAD_REQUEST, SUCCESS

SOURCE = "/api/items/filter_item_prices"

def response_log(custom_message, code, error, response_message=None):
    return _respond(
        body={},
        custom_message=custom_message,
        ipaddress=request.remote_addr,
        response_message=response_message,
        source="service",
        log_type="Filter prices",
        message_code=f"PP{code}",
        log_status=code,
        error=error
    )

def filter_items_prices():
    response_log("Entered in filter price function", INITIATING_FUNCTION, False)
    data = request.get_json()
    if not data:
        response_log("Request body is empty", BAD_REQUEST, False)
        return marshal_response_msg({
            "error_message" : "Not found",
            "error_details" : "Request body is empty, please provid a valid request body",
            "error_code" : BAD_REQUEST,
            "is_error" : True
        })
    data, error = filter_price_data(data)
    if error['error']:
        return marshal_response_msg({
            "error_message" : "No data founded",
            "error_details" : "Something went wrong, can't filter items prices datas",
            "error_code" : error['error_code'],
            "is_error" : True,
            "custom_field" : {
                "page" : error['page'],
                "limit" : error['limit'],
                "total" : error['total']
            }
        })
    response_log("Filter price function completed", SUCCESS, False)
    return marshal_response_msg({
        "data" : data['data'],
        "success_message" : "Successfully select price data",
        "success_code" : SUCCESS,
        "source" : SOURCE,
        "is_error" : False,
        "custom_field" : {
            "page" : data['page'],
            "limit" : data['limit'],
            "total" : data['total']
        }
    })