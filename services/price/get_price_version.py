from flask import request
from repository.price.fetch_ho_price_records_by_version import get_prices_from_version
from repository.price.select_one_site import select_one_site
from utils.log_response import _respond
from data.error_codes import INITIATING_FUNCTION, SUCCESS, BAD_REQUEST, NOT_FOUND
from data.response import marshal_response_msg

SOURCE = "/api/items/prices/version/"

def response_log(custom_message, code, error, response_message=None):
    return _respond(
        body={},
        custom_message=custom_message,
        ipaddress=request.remote_addr,
        response_message=response_message,
        source="service",
        log_type="Fetch HO price by version",
        message_code=f"PP{code}",
        log_status=code,
        error=error
    )

def get_price_version(version_id, site_code, skip):
    response_log("Enter into fetch ho price by version", INITIATING_FUNCTION, False)

    if version_id is None or version_id == "":
        response_log("Version Id not found", BAD_REQUEST, True)
        return marshal_response_msg({
            "error_message" : "Version Id not found",
            "error_details" : "Version id is required, but not given, please provide a valid version id",
            "error_code" : BAD_REQUEST,
            "is_error" : True
        })

    if site_code is None or site_code == "":
        response_log("Site code not found", BAD_REQUEST, True)
        return marshal_response_msg({
            "error_message" : "Site code not found",
            "error_details" : "Site code is required, but not given, please provide a valid site code",
            "error_code" : BAD_REQUEST,
            "is_error" : True
        })

    
    site_data, site_error = select_one_site(site_code)
    if site_error['error']:
        return marshal_response_msg({
            "error_message" : "No site data found for this site code",
            "error_details" : "There is no site data in the site code",
            "error_code" : site_error['error_code'],
            "is_error" : True
        })

    if site_data[0]['active'] != 1:
        return marshal_response_msg({
            "error_message" : "The site in this code is temporarily deactive",
            "error_details" : "The site is deactive",
            "error_code" : NOT_FOUND,
            "is_error" : True
        })

    data, error = get_prices_from_version(version_id, site_code, skip)

    if error['error']:
        return marshal_response_msg({
            "error_message" : "No data found",
            "error_details" : "There is no data in the condition",
            "error_code" : error['error_code'],
            "is_error" : True
        })
    
    response_log("Completed HO price fetch completed", SUCCESS, False)
    return marshal_response_msg({
        "data" : data['data'],
        "success_message" : "Successfully selected price by version",
        "success_code" : error['error_code'],
        "source" : SOURCE,
        "is_error" : False,
        "custom_field" : {
            "version_id" : data['version_id'],
            "count" : data['count']
        }
    })