from flask import request, jsonify
from repository.discount.filter_discount_data import filter_discount_data
from utils.log_response import _respond
from data.error_codes import INITIATING_FUNCTION, BAD_REQUEST, SUCCESS


def response_log(custom_message, code, error, response_message=None):
    return _respond(
        body={},
        custom_message=custom_message,
        ipaddress=request.remote_addr,
        response_message=response_message,
        source="service",
        log_type="Filter discounts",
        message_code=f"PP{code}",
        log_status=code,
        error=error,
    )


def filter_items_discount():
    response_log("Entered in filter discount function", INITIATING_FUNCTION, False)

    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        response_log("Request body is empty", BAD_REQUEST, True)
        return jsonify({
            "status": "error",
            "message": "Request must contain a valid JSON object",
        }), BAD_REQUEST

    body, status = filter_discount_data(data)

    if status == 200:
        response_log("Filter discount function completed", SUCCESS, False)

    return jsonify(body), status