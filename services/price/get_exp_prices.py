from flask import request
from repository.price.fetch_all_expired_prices import fetch_all_expired_prices
from utils.log_response import _respond
from data.error_codes import INITIATING_FUNCTION, SUCCESS, NOT_FOUND
from data.response import marshal_response_msg

SOURCE = "/api/items/fetch_all_expired_prices"

def response_log(custom_message, code, error, response_message=None):
    return _respond(
        body={},
        custom_message=custom_message,
        ipaddress=request.remote_addr,
        response_message=response_message,
        source="service",
        log_type="Fetch all pexpired rice",
        message_code=f"PP{code}",
        log_status=code,
        error=error
    )

def get_exp_prices():
    response_log("Entered in fetch all expired price function", INITIATING_FUNCTION, False)
    data, error = fetch_all_expired_prices()
    if error['error']:
        return marshal_response_msg({
            "error_message" : "No data founded",
            "error_details" : "Something went wrong, can't select expired items prices datas",
            "error_code" : error['error_code'],
            "is_error" : True,
            "custom_field" : {
                "page" : error['page'],
                "limit" : error['limit'],
                "total_records" : error['total_records']
            }
        })
    response_log("Fetch all expired price function completed", SUCCESS, False)
    return marshal_response_msg({
        "data" : data['data'],
        "success_message" : "Successfully selected expired item datas",
        "success_code" : error['error_code'],
        "source" : SOURCE,
        "is_error" : False,
        "custom_field" : {
            "page" : data['page'],
            "limit" : data['limit'],
            "total_records" : data['total_records']
        }
    })