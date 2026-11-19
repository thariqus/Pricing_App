from flask import request
import requests
from repository.price.fetch_price import fetch_all_prices
from repository.price.get_replication_version import get_replication_version_data
from repository.price.get_ho_version_count import get_ho_version_count
from repository.price.get_one_site_data import get_one_site_data
from data.response import marshal_response_msg
from data.error_codes import SUCCESS
from utils.log_response import _respond
from data.error_codes import INITIATING_FUNCTION, BAD_REQUEST, SUCCESS, INTERNAL_SERVER_ERROR

import os

SOURCE = "/site-details/"

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

    if not site:
        response_log("site code not found", BAD_REQUEST, True)
        return marshal_response_msg({
            "error_message" : "Site code not found",
            "error_details" : "Site code is required, please provide a valid site code",
            "error_code" : BAD_REQUEST,
            "is_error" : True
        })

    version_data, version_error = get_replication_version_data(site)
    if version_error['error']:
        return marshal_response_msg({
            "error_message" : "Can't fetch version data",
            "error_details" : "Something went wrong can't fetch the version data",
            "error_code" : version_error['error_code'],
            "is_error" : True
        })

    site_data, site_error = get_one_site_data(site)
    if site_error['error']:
        return marshal_response_msg({
            "error_message" : "Can't fetch site data",
            "error_details" : "Something went wrong can't fetch the site data, site data is required, but its missing or not added",
            "error_code" : site_error['error_code'],
            "is_error" : True
        })

    response = requests.get(
        f"{site_data[0]['site_ip']}/api/items/get_repliaction_data/{version_data}/{site}",
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
        ho_data, ho_error = get_ho_version_count(count['version_id'], site)
        if ho_error['error']:
            response_log("Error in get ho version count call", INTERNAL_SERVER_ERROR, True)
            return marshal_response_msg({
                "error_message" : "Error in version count call",
                "error_details" : "Something went wrong, can't complete the process",
                "error_code" : ho_error['error_code'],
                "is_error" : True
            })

        if ho_data[0]["version_count"] == count['version_count']:
            final_version = count['version_id']

    price_data, price_error = fetch_all_prices()
    if price_error['error']:
        return marshal_response_msg({
            "error_message" : "No data founded",
            "error_details" : "Something went wrong, can't select items prices datas",
            "error_code" : price_error['error_code'],
            "is_error" : True,
            "custom_field" : {
                "page" : price_error['page'],
                "limit" : price_error['limit'],
                "total_records" : price_error['total_records']
            }
        })

    filtered_data = [
        {**row, 'status': 'Failed'}
        for row in price_data['data']
        if row['version_id'] > final_version and (row['location_code'] == site or row['location_code'] == None)
    ]

    response_log("Store to ho data function completed", SUCCESS, False)
    return marshal_response_msg({
        "data" : filtered_data,
        "success_message" : "Successfully selected",
        "success_code" : SUCCESS,
        "source" : SOURCE,
        "is_error" : False,
        "custom_field" : {
            "store_ip" : site_data[0]['site_ip']
        }
    })