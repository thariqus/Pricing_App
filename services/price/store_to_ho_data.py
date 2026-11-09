from flask import request
import requests
from repository.price.fetch_price import fetch_all_prices
from repository.price.get_replication_version import get_replication_version_data
from repository.price.get_ho_version_count import get_ho_version_count
from data.response import marshal_response_msg
from data.error_codes import SUCCESS
from utils.log_response import _respond
from data.error_codes import INITIATING_FUNCTION, BAD_REQUEST, SUCCESS

import os

SOURCE = "/site-details/"
STORE_URL = os.getenv("STORE_1_URL")

def response_log(custom_message, code, error, response_message=None):
    return _respond(
        body={},
        custom_message=custom_message,
        ipaddress=request.remote_addr,
        response_message=response_message,
        source="service",
        log_type="Store to HO data",
        message_code=f"PP{code}",
        log_status=code,
        error=error
    )

def store_to_ho_data(site):
    response_log("Entered in store to ho data function", INITIATING_FUNCTION, False)

    version = get_replication_version_data(site)['response']['custom_fields']['version']

    response = requests.get(
        f"{STORE_URL}/api/items/get_repliaction_data/{version}/{site}",
        timeout=10
    )
    if not response.ok:
        response_log("Error in API call", BAD_REQUEST, True)
        return marshal_response_msg({
            "error_message" : "Error in API call",
            "error_details" : "Error occure when API call",
            "error_code" : BAD_REQUEST,
            "is_error" : True
        })

    # response data
    response_data = response.json()['response']['data']

    # remove duplication
    store_counts = list({
        row['version_id']: {
            "version_id": row['version_id'],
            "version_count": row['version_count']
        }
        for row in response_data
    }.values())

    final_version = 0

    for count in store_counts:
        ho_data = get_ho_version_count(count['version_id'], site)
        if ho_data[0]["version_count"] == count['version_count']:
            final_version = count['version_id']

    ho_data_json = fetch_all_prices()['response']['data']

    filtered_data = [
        {**row, 'status': 'Failed'}
        for row in ho_data_json
        if row['version_id'] > final_version
    ]

    response_log("Store to ho data function completed", SUCCESS, False)
    return marshal_response_msg({
        "data" : filtered_data,
        "success_message" : "Successfully selected",
        "success_code" : SUCCESS,
        "source" : SOURCE,
        "is_error" : False
    })