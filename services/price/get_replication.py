from flask import request
from repository.price.get_replication_store_data import get_replication_store_data
from utils.log_response import _respond
from data.error_codes import INITIATING_FUNCTION, SUCCESS

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
    data = get_replication_store_data(version_id, site_id)
    if data['response']['is_error']:
        return data
    response_log("Get replication function completed", SUCCESS, False)
    return data