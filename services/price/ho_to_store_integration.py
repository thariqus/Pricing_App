from flask import request
import requests
from configration.integration_ip import HEAD_OFFICE
from repository.price.get_all_site_data import get_all_site_data
from data.response import marshal_response_msg
from data.error_codes import SUCCESS, INITIATING_FUNCTION
from utils.log_response import _respond

SOURCE = "/api/items/integration_check"

def response_log(custom_message, code, error, response_message=None):
    return _respond(
        body={},
        custom_message=custom_message,
        ipaddress=request.remote_addr,
        response_message=response_message,
        source="service",
        log_type="HO to store integration",
        message_code=f"PP{code}",
        log_status=code,
        error=error
    )

def check_site(site):
    try:
        response = requests.post(
            f"{site['ip']}/api/items/fetch_all_item_prices",
            timeout=10
        )
        if response.ok:
            site["status"] = "connected"
        else:
            site["status"] = "disconnected"

    except requests.exceptions.ConnectionError as e:
        site["status"] = "disconnected"

    except requests.exceptions.Timeout as e:
        site["status"] = "disconnected"

    except requests.exceptions.RequestException as e:
        site["status"] = "disconnected"

    return site
    

def ho_to_store_integration():
    response_log("Entered in HO to store integration function", INITIATING_FUNCTION, False)
    SITES = []
    data, error = get_all_site_data()
    if error['error']:
        return marshal_response_msg({
            "error_message" : "No data founded",
            "error_details" : "Something went wrong, can't select site datas",
            "error_code" : error['error_code'],
            "is_error" : True
        })
    for sites in data:
        SITES.append(check_site({"ip" : sites['site_ip'], "code" : sites['site_location']}))
    response_log("HO to store integration function completed", SUCCESS, False)
    return marshal_response_msg({
        "success_message" : "Site selected successfully",
        "success_code" : SUCCESS,
        "source" : SOURCE,
        "is_error" : False,
        "custom_field" : {
            "sites": SITES,
            "head" : HEAD_OFFICE
        }
    })