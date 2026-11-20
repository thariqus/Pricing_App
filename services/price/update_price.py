import os
from flask import request
from repository.price.update_price import update_price_data
from data.response import marshal_response_msg
from utils.log_response import _respond
from data.error_codes import INITIATING_FUNCTION, SUCCESS, BAD_REQUEST, UNAUTHORIZED
from utils.classes.price_body_validator import PriceConditionValidator

SOURCE = "/api/items/update_item_prices/"
IS_CENTRAL = os.getenv("IS_CENTRAL")

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
    if IS_CENTRAL != "1":
        return marshal_response_msg({
            "error_message" : "Permission Denided",
            "error_details" : "Request user is store and they have no permission to edit",
            "error_code" : UNAUTHORIZED,
            "is_error" : True
        })
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
    data, error = update_price_data(data)
    if error['error']:
        return marshal_response_msg({
            "error_message" : "No data founded",
            "error_details" : "Something went wrong, can't select items prices datas",
            "error_code" : error['error_code'],
            "is_error" : True,
            "custom_field" : {
                "page" : error['page'],
                "limit" : error['limit'],
                "total_records" : error['total_records']
            }
        })
    response_log("Update price function completed", SUCCESS, False)
    return marshal_response_msg({
        "data" : data['data'],
        "success_message" : "Price update completed",
        "success_code" : error['error_code'],
        "source" : SOURCE,
        "is_error" : False,
        "custom_field" : {
            "updated_count": data['updated_count'],
            "failed_count": data['failed_count'],
            "failed": data['failed']
        }
    })
        