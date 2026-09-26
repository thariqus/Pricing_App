from flask import request, jsonify
import requests
from utils.date_converter import convert_datetime
from repository.price.create_single_price import create_single_price
from utils.log_error import logger
import os
VALIDATION_API = os.getenv("VALIDATION_API")

def create_single_item_price():
    data = request.get_json()
    if not data:
        return ({
            "status" : "error",
            "message": "Request body is empty"
        }), 400
    validation_records = [
        {
            "item_code": data.get("item_no"),
            "uom": data.get("uom")
        }
    ]
    response = requests.post(
        VALIDATION_API,
        json=validation_records,
        timeout=60
    )
    response_message = response.json()
    items_no = response_message["message"]["item"]["non_existent"]
    uoms = response_message["message"]["item_uoms"]["non_existent"]
    if items_no:
        return {
            "status": "error",
            "message": "Item not found"
        }
    if uoms:
        return {
            "status": "error",
            "message": "UOM not found"
        }
    else:
        formatted_data = convert_datetime(data)
        mysql = create_single_price(formatted_data)
        return mysql