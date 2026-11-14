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
            return render_template(
                "index.html",
                message="No file selected",
                message_type="error"
            )

        csv_record, file = upload_csv(file)
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
        
        mysql = ho_create_price(valid_data, file, invalid_data)
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

        response_log("Create price function completed", SUCCESS, False)
        return mysql
    else:
        return marshal_response_msg({
            "error_message" : "Permission error",
            "error_details" : "NO permission to upload",
            "error_code" : UNAUTHORIZED,
            "is_error" : True
        })