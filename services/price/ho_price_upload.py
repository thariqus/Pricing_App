import http

from flask import request, render_template, jsonify
import requests
import os
from data.csv_upload.price_csv_upload import upload_csv
from repository.price.ho_create_price import ho_create_price
from data.csv_upload.price_csv_check import check_price_csv_items
import json
from concurrent.futures import ThreadPoolExecutor
from repository.price.get_all_site_data import get_all_site_data

from utils.log_error import logger
import threading





IS_CENTRAL = os.getenv("IS_CENTRAL")
VALIDATION_API = os.getenv("VALIDATION_API")


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
            return jsonify({
                "status": "error",
                "message": "CSV file contains no records"
            }), 400
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
        response_message = response.json()
        valid_data, invalid_data = check_price_csv_items(csv_record, response_message)
        
        mysql = ho_create_price(valid_data, file, invalid_data)
        if mysql is False:
            return jsonify({
                "status": "error",
                "message": "Failed to create HO prices"
            }), 500

        results = []

        sites_data = get_all_site_data()['data']
        SITES= [
            sites['site_ip'] for sites in sites_data
        ]
        with ThreadPoolExecutor(max_workers=5) as executor:
            result = executor.map(
                call_apis,
                SITES
            )
            results.extend(result)
        
        return mysql
    else:
        return jsonify({
            "status": "error",
            "message": "NO permission to upload"
        })