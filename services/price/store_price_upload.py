import os
import requests
from repository.price.fetch_store_pricing_version import (
    get_latest_version_id,
    get_version_record_count,
)
from repository.price.store_price_upload import store_create_price
from data.response import marshal_response_msg
from data.error_codes import BAD_REQUEST

HO_URL = os.getenv("HO_URL")
STORE_SITE_CODE = os.getenv("STORE_SITE_CODE")
SOURCE = ""


def get_latest_version():
    return int(get_latest_version_id() or 0)


def latest_update(version, skip):
    response = requests.get(
        f"{HO_URL}/api/items/prices/version/{version}",
        params={"skip": skip, "site_code": STORE_SITE_CODE},
    )
    response.raise_for_status()
    return response.json()


def replication_main():
    latest_version = get_latest_version()
    new_version = latest_version + 1 if latest_version else 0
    skip = get_version_record_count(new_version) if new_version else 0

    records = latest_update(latest_version, skip).get("response", {}).get("data", [])
    if not records:
        return None

    if not records:
        return marshal_response_msg({
            "error_message" : "No Records found",
            "error_details" : "Records is required, but not given",
            "error_code" : BAD_REQUEST,
            "is_error" : True
        })

    data, error = store_create_price(records)
    if error['error']:
        return marshal_response_msg({
            "error_message" : "Data not edited..",
            "error_details" : "Something went wrong, Data is not edited..",
            "error_code" : error['error_code'],
            "is_error" : True
        })
    
    return marshal_response_msg({
        "success_message" : "Successfully created",
        "success_code" : error['error_code'],
        "source" : SOURCE,
        "is_error" : False,
        "custom_field" : {
            "inserted" : data['inserted']
        }
    })


def run_replication(app):
    with app.app_context():
        replication_main()