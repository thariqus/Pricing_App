from flask import request, render_template, jsonify
import requests
import os
from data.csv_upload.price_csv_upload import upload_csv
from repository.price.ho_create_price import ho_create_price
from data.csv_upload.price_csv_check import check_price_csv_items
IS_CENTRAL = os.getenv("IS_CENTRAL")
VALIDATION_API = os.getenv("VALIDATION_API")

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
            json=validation_records,
            timeout=60
        )
        response_message = response.json()
        valid_data, invalid_data = check_price_csv_items(csv_record, response_message)
        mysql = ho_create_price(valid_data, file, invalid_data)
        return mysql
    else:
        return jsonify({
            "status": "error",
            "message": "NO permission to upload"
        })