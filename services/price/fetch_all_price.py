from flask import request
from repository.price.fetch_price import fetch_all_prices
from utils.log_response import _respond
from data.error_codes import INITIATING_FUNCTION, SUCCESS

def response_log(custom_message, code, error, response_message=None):
    return _respond(
        body={},
        custom_message=custom_message,
        ipaddress=request.remote_addr,
        response_message=response_message,
        source="service",
        log_type="Fetch all price",
        message_code=f"PP{code}",
        log_status=code,
        error=error
    )

def fetch_all_items_prices():
    response_log("Entered in fetch all price function", INITIATING_FUNCTION, False)
    datas = fetch_all_prices()
    if datas['response']['is_error']:
        return datas
    response_log("Fetch all price function completed", SUCCESS, False)
    return datas