from flask import request, render_template
import requests
import os
from data.csv_upload.price_csv_upload import upload_csv
from repository.price.ho_create_price import ho_create_price
from data.csv_upload.price_csv_check import check_price_csv_items
from concurrent.futures import ThreadPoolExecutor
from repository.price.get_all_site_data import get_all_site_data
from data.response import marshal_response_msg
from data.error_codes import BAD_REQUEST, UNAUTHORIZED, INITIATING_FUNCTION, SUCCESS, INTERNAL_SERVER_ERROR
from utils.log_response import _respond
from utils.classes.price_body_validator import PriceConditionValidator

SOURCE = "/api/items/store_csv_uploads"


IS_CENTRAL = os.getenv("IS_CENTRAL")
VALIDATION_API = os.getenv("VALIDATION_API")

def response_log(custom_message, code, error, response_message=None):
    return _respond(
        body={},
        custom_message=custom_message,
        ipaddress=request.remote_addr,
        response_message=response_message,
        source="service",
        log_type="HO price upload",
        message_code=f"PP{code}",
        log_status=code,
        error=error
    )

# should be on utlis
def _is_blank_row(row):
    # 'active' is always filled by upload_csv, so ignore it
    return all(
        value is None or str(value).strip() == ""
        for key, value in row.items()
        if key != "active"
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

def ho_price_upload():
    response_log("Entered in HO price upload function", INITIATING_FUNCTION, False)
    if IS_CENTRAL == '1':
        file = request.files.get("file")

        if not file:
            response_log("Request body is empty", BAD_REQUEST, True)
            return marshal_response_msg({
                "error_message" : "Data not found",
                "error_details" : "Request body is empty, give a valid json",
                "error_code" : BAD_REQUEST,
                "is_error" : True,
            })

        csv_data, csv_error = upload_csv(file)
        if csv_error['error']:
            return marshal_response_msg({
                "error_message" : "Data proccess error",
                "error_details" : "Something went wrong, data can't process",
                "error_code" : csv_error['error_code'],
                "is_error" : True,
            })
        csv_record = csv_data['records']
        file = csv_data['file']
        csv_record = [row for row in (csv_record or []) if not _is_blank_row(row)]

        if not csv_record:
            response_log("CSV file contains no records", BAD_REQUEST, True)
            return marshal_response_msg({
                "error_message" : "Empty CSV",
                "error_details" : "CSV file contains no records",
                "error_code" : BAD_REQUEST,
                "is_error" : True
            })
        
        validation_records = [
            {
                "item_code": data.get("item_no"),
                "uom": data.get("uom")
            }
            for data in csv_record
        ]
        response = requests.post(
            VALIDATION_API,
            json=validation_records
            # timeout=60
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
        valid_data, invalid_data = check_price_csv_items(csv_record, response_message)

        # try:
        #     valid_data = PriceConditionValidator(valid_data).validate()
        # except Exception as e:
        #     return marshal_response_msg({
        #         "error_message" : "Validation Error",
        #         "error_details" : str(e),
        #         "error_code" : INTERNAL_SERVER_ERROR,
        #         "is_error" : True,
        #     })
        if not valid_data:
            response_log("No records found", BAD_REQUEST, True)
            return marshal_response_msg({
                "error_message" : "Not found",
                "error_details" : "Records is required, but not given",
                "error_code" : BAD_REQUEST,
                "is_error" : True
            })
        data, error = ho_create_price(valid_data, file, invalid_data)
        if error['error']:
            return marshal_response_msg({
                "error_message" : "Inseration failed",
                "error_details" : f"Somehing went wrong, can't insert the records",
                "error_code" : error['error_code'],
                "is_error" : True
            })
        if IS_CENTRAL == '1':
            results = []

            sites_data, site_error = get_all_site_data()
            if site_error['error']:
                return marshal_response_msg({
                    "error_message" : "Data added, but can't select site datas, site data is missing, replication is failed",
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

        response_log("Create price function completed", SUCCESS, False)
        return marshal_response_msg({
            "success_message" : f"{data['count']} price(s) inserted, {data['deactivated']} old price(s) deactivated",
            "success_code" : error['error_code'],
            "source" : SOURCE,
            "is_error" : False,
            "custom_field" : {
                "count": data['count'],
                "deactivated": data['deactivated'],
                "InvalidData": data['InvalidData']
            }
        })
    else:
        return marshal_response_msg({
            "error_message" : "Permission error",
            "error_details" : "NO permission to upload",
            "error_code" : UNAUTHORIZED,
            "is_error" : True
        })