import os
from flask import request, render_template, jsonify
import requests
from data.csv_upload.discount_csv_upload import upload_discount_csv
from repository.discount.ho_create_discount import ho_create_discount
from data.csv_upload.discount_csv_check import check_discount_csv_items
from concurrent.futures import ThreadPoolExecutor
from configration.integration_ip import SITES

from utils.log_error import logger


IS_CENTRAL = os.getenv("IS_CENTRAL")
VALIDATION_API = os.getenv("VALIDATION_API")


def _is_blank_row(row):
    # 'active' is always filled by upload_csv, so ignore it
    return all(
        value is None or str(value).strip() == ""
        for key, value in row.items()
        if key != "active"
    )


def call_apis(api_name):
    url = f"{api_name}/api/items/notify_discount_stores"

    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()

        return response.json()

    except Exception as e:
        return {
            "error": str(e),
            "api": url
        }


def ho_discount_upload():

    if IS_CENTRAL == '1':
        file = request.files.get("file")

        if not file:
            return render_template(
                "index.html",
                message="No file selected",
                message_type="error"
            )

        csv_record, file = upload_discount_csv(file)
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
        )
        response_message = response.json()
        valid_data, invalid_data = check_discount_csv_items(csv_record, response_message)

        mysql = ho_create_discount(valid_data, file, invalid_data)
        if mysql is False:
            return jsonify({
                "status": "error",
                "message": "Failed to create HO discounts"
            }), 500

        results = []
        with ThreadPoolExecutor(max_workers=5) as executor:
            result = executor.map(
                call_apis,
                SITES
            )
            results.extend(result)
        print("Results from API calls:", results)

        return mysql

    else:
        return jsonify({
            "status": "error",
            "message": "NO permission to upload"
        }), 403