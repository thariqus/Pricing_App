from flask import request, jsonify
from utils.log_error import logger
from repository.discount.update_discount import update_discount_data


def update_item_discount():
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
    return update_discount_data(data)