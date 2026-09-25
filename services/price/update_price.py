from flask import request, jsonify
from utils.log_error import logger
from repository.price.update_price import update_price_data

def update_item_price():
    data = request.get_json()
    if isinstance(data, dict):
                data = [data]
    if not isinstance(data, list):
        return jsonify({
            "status": "error",
            "message": "Request body must be an object or list of objects"
        }), 400
    if not data:
        return jsonify({
            "status": "error",
            "message": "No update data received"
        }), 400
    mysql = update_price_data(data)
    return mysql
        