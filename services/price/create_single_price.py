from flask import request
import requests
from utils.date_converter import convert_datetime
from repository.price.create_single_price import create_single_price
import os
from concurrent.futures import ThreadPoolExecutor
from repository.price.get_all_site_data import get_all_site_data
from data.response import marshal_response_msg
from utils.log_response import _respond
from data.error_codes import INITIATING_FUNCTION, BAD_REQUEST, NOT_FOUND, SUCCESS

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

    data = request.get_json()
    if not data:
        response_log("Request body is empty", BAD_REQUEST, True)
        return marshal_response_msg({
            "error_message" : "Not found",
            "error_details" : "Request body is empty, give a valid json",
            "error_code" : BAD_REQUEST,
            "is_error" : True,
        })
    validation_records = [
        {
            "item_code": data.get("item_no"),
            "uom": data.get("uom")
        }
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
    if items_no:
        response_log("Item not found", NOT_FOUND, True)
        return marshal_response_msg({
            "error_message" : "Not found",
            "error_details" : "Item not found",
            "error_code" : NOT_FOUND,
            "is_error" : True,
        })
    if uoms:
        response_log("UOM not found", NOT_FOUND, True)
        return marshal_response_msg({
            "error_message" : "Not found",
            "error_details" : "UOM not found",
            "error_code" : NOT_FOUND,
            "is_error" : True,
        })
    else:
        formatted_data = convert_datetime(data)
        mysql = create_single_price(formatted_data)
        if mysql['response']['is_error']:
            return mysql
        results = []
        sites_data = get_all_site_data()['response']['data']
        SITES= [
            sites['site_ip'] for sites in sites_data
        ]
        with ThreadPoolExecutor(max_workers=5) as executor:
            result = executor.map(
                call_apis,
                SITES
            )
            results.extend(result)
        response_log("Create single price function completed", SUCCESS, False)
        return mysql