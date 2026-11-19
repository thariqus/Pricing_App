from flask import request
import requests
from utils.date_converter import convert_datetime_single_item
from repository.price.create_single_price import create_single_price
import os
from concurrent.futures import ThreadPoolExecutor
from repository.price.get_all_site_data import get_all_site_data
from data.response import marshal_response_msg
from utils.log_response import _respond
from data.error_codes import INITIATING_FUNCTION, BAD_REQUEST, NOT_FOUND, SUCCESS, INTERNAL_SERVER_ERROR, UNAUTHORIZED
from utils.classes.price_body_validator import PriceConditionValidator

IS_CENTRAL = os.getenv("IS_CENTRAL")
SOURCE = "/api/items/create_singel_item_price"

VALIDATION_API = os.getenv("VALIDATION_API")

def response_log(custom_message, code, error, response_message=None):
    return _respond(
        body={},
        custom_message=custom_message,
        ipaddress=request.remote_addr,
        response_message=response_message,
        source="service",
        log_type="Create single price",
        message_code=f"PP{code}",
        log_status=code,
        error=error
    )

def call_apis(api_name):
    url = f"{api_name}/api/items/notify_stores"

    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()

        return response.json()

    except Exception as e:
        return {
            "error": str(e),
            "api": url
        }

def create_single_item_price():
    response_log("Entered in create single price function", INITIATING_FUNCTION, False)

    if IS_CENTRAL != "1":
        return marshal_response_msg({
            "error_message" : "Permission Denided",
            "error_details" : "Request user is store and they have no permission to edit",
            "error_code" : UNAUTHORIZED,
            "is_error" : True
        })

    data = request.get_json()
    if not data:
        response_log("Request body is empty", BAD_REQUEST, True)
        return marshal_response_msg({
            "error_message" : "Data not found",
            "error_details" : "Request body is empty, give a valid json",
            "error_code" : BAD_REQUEST,
            "is_error" : True,
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
    validation_records = [
        {
            "item_code": items.get("item_no"),
            "uom": items.get("uom")
        }
        for items in data
    ]
    response = requests.post(
        VALIDATION_API,
        json=validation_records,
        timeout=60
    )
    if not response.ok:
        response_log("API call error", BAD_REQUEST, True)
        return marshal_response_msg({
            "error_message" : "API call error",
            "error_details" : "Error occure when API called",
            "error_code" : BAD_REQUEST,
            "is_error" : True,
        })

    response_message = response.json()
    items_no = response_message["message"]["item"]["non_existent"]
    uoms = response_message["message"]["item_uoms"]["non_existent"]
    if items_no or uoms:
        response_log("Item or UOM not found", NOT_FOUND, True)
        return marshal_response_msg({
            "error_message" : "Item or UOM is not found or mismatched, please check it and retry..",
            "error_details" : "Item or UOM not found or mismatch",
            "error_code" : NOT_FOUND,
            "is_error" : True,
        })
    else:
        formatted_data = convert_datetime_single_item(data)
        if not formatted_data:
            response_log("Error in the date conversion", INTERNAL_SERVER_ERROR, True)
            return marshal_response_msg({
                "error_message" : "Date conversion error",
                "error_details" : "Something went wrong, error in the date conversion",
                "error_code" : INTERNAL_SERVER_ERROR,
                "is_error" : True
            })
        insert_data, error = create_single_price(formatted_data)
        if error['error']:
            return marshal_response_msg({
                "error_message" : "Data not inserted",
                "error_details" : "Something went wrong, can't insert the current item",
                "error_code" : INTERNAL_SERVER_ERROR,
                "is_error" : True
            })
        if IS_CENTRAL == '1':
            results = []
            sites_data, site_error = get_all_site_data()
            if site_error['error']:
                return marshal_response_msg({
                    "error_message" : "Can't select site datas, site data is missing, replication is failed",
                    "error_details" : "Something went wrong, can't select the site datas",
                    "error_code" : INTERNAL_SERVER_ERROR,
                    "is_error" : True
                })
            SITES= [
                sites['site_ip'] for sites in sites_data if sites["active"] == 1
            ]
            with ThreadPoolExecutor(max_workers=5) as executor:
                result = executor.map(
                    call_apis,
                    SITES
                )
                results.extend(result)
        response_log("Create single price function completed", SUCCESS, False)
        return marshal_response_msg({
            "success_message" : f"{insert_data} records created successfully",
            "success_code" : error['error_code'],
            "source" : SOURCE,
            "is_error" : False
        })