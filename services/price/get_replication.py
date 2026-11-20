from flask import request
from repository.price.get_replication_store_data import get_replication_store_data
from utils.log_response import _respond
from data.error_codes import INITIATING_FUNCTION, SUCCESS, BAD_REQUEST, NOT_FOUND
from data.response import marshal_response_msg

SOURCE = "/api/items/get_repliaction_data/"

def response_log(custom_message, code, error, response_message=None):
    return _respond(
        body={},
        custom_message=custom_message,
        ipaddress=request.remote_addr,
        response_message=response_message,
        source="service",
        log_type="Get all replication",
        message_code=f"PP{code}",
        log_status=code,
        error=error
    )

def get_replication(version_id, site_id):
    response_log("Entered in get replication function", INITIATING_FUNCTION, False)
    if version_id is None or version_id == "":
        response_log("Version id not found", BAD_REQUEST, True)
        return marshal_response_msg({
            "error_message" : "Version Id not found",
            "error_details" : "Version Id is required, please give a valid version Id",
            "error_code" : BAD_REQUEST,
            "is_error" : True
        })

    if site_id is None or site_id == "":
        response_log("Site code not found", BAD_REQUEST, True)
        return marshal_response_msg({
            "error_message" : "Site code not found",
            "error_details" : "Site code is required, please give a valid site code",
            "error_code" : BAD_REQUEST,
            "is_error" : True
        })
    data, error = get_replication_store_data(version_id, site_id)
    if error['error']:
        return marshal_response_msg({
            "error_message" : "No data found",
            "error_details" : f"No data found based {version_id} version in {site_id} store",
            "error_code" : NOT_FOUND,
            "is_error" : True
        })
    response_log("Get replication function completed", SUCCESS, False)
    return marshal_response_msg({
        "data" : data,
        "success_message" : "Successfully selected replication data",
        "success_code" : SUCCESS,
        "source" : SOURCE,
        "is_error" : False
    })