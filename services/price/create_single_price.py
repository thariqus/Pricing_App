from flask import request
from utils.date_converter import convert_datetime
from repository.price.create_single_price import create_single_price
from utils.log_error import logger

def create_single_item_price():
    logger.info("Entre into single item price")
    logger.info("Getting Data")
    data = request.get_json()
    if not data:
        return ({
            "status" : "error",
            "message": "Request body is empty"
        }), 400
    logger.info("Converter Dates")
    formatted_data = convert_datetime(data)
    logger.info("Calling insert function")
    mysql = create_single_price(formatted_data)
    logger.info("Return response")
    return mysql