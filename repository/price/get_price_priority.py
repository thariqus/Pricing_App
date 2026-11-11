from flask import request
from repository.mysql_connection import get_db_connection
import pymysql
from utils.log_response import _respond
import os
from data.error_codes import (
    INITIATING_FUNCTION,
    BAD_REQUEST,
    SUCCESS,
    SERVICE_UNAVAILABLE,
    INTERNAL_SERVER_ERROR,
    NOT_FOUND,
    NOT_IMPLEMENTED
)
from data.structure.combination_rule import PRIORITY_RULES, FIELD_MAP
from repository.query import _price_query
from data.response import marshal_response_msg

SOURCE = "/api/get_discounted_item_price"


def response_log(custom_message, code, error, response_message=None):
    return _respond(
        body={},
        custom_message=custom_message,
        ipaddress=request.remote_addr,
        response_message=response_message,
        source="repository",
        log_type="Get price priority",
        message_code=f"PP{code}",
        log_status=code,
        error=error
    )

def _val(data, key):
    """Trimmed string value, or None if missing/empty."""
    value = data.get(key)
    if value is None:
        return None
    value = str(value).strip()
    return value or None


def _key_val(data, key):
    """Like _val, but 0 / '0' also counts as not provided."""
    value = _val(data, key)
    if value is None or value == "0":
        return None
    return value

def get_price_priority(data):
    con = None
    cursor = None


    response_log("Entered in getprice priority function", INITIATING_FUNCTION, False)
    try:
        if not data or not isinstance(data, dict):
            response_log("Request data is empty or invalid", BAD_REQUEST, True)
            return marshal_response_msg({
                "error_message" : "Request data is empty or invalid",
                "error_details" : "Give data is invalid, please provide a valid data",
                "error_code" : BAD_REQUEST,
                "is_error" : True
            })

        item_no = _val(data, "item_no")
        uom = _val(data, "unit_of_measure_code")

        context = (
            f"Price lookup item={item_no} "
            f"uom={uom} qty={data.get('qty')}"
        )

        if not item_no or not uom:
            response_log("item_no and unit_of_measure_code are required", BAD_REQUEST, True)
            return marshal_response_msg({
                "error_message" : "Invalid request",
                "error_details" : "Item no and UOM are required, there are not provided, please provide it",
                "error_code" : BAD_REQUEST,
                "is_error" : True
            })

        try:
            quantity = float(_val(data, "qty") or 1)
        except (ValueError, TypeError):
            response_log("Quanty must be a number", BAD_REQUEST, True)
            return marshal_response_msg({
                "error_message" : "Value error",
                "error_details" : "Quantity must be a number",
                "error_code" : BAD_REQUEST,
                "is_error" : True
            })

        # Values provided by the caller, keyed by DB column
        provided = {
            col: _key_val(data, key)
            for key, col in FIELD_MAP.items()
        }

        con = get_db_connection(os.getenv("DB_P_NAME"))
        cursor = con.cursor()

        result = None
        matched_priority = None
        checked = []

        for priority, key_columns in PRIORITY_RULES:

            # Skip priorities whose key fields were not supplied
            if any(provided[col] is None for col in key_columns):
                continue

            checked.append(priority)

            params = (
                [priority, item_no, uom, quantity]
                + [provided[col] for col in key_columns]
            )

            cursor.execute(_price_query(key_columns), params)
            row = cursor.fetchone()

            if row:
                result = row
                matched_priority = priority
                break

        if not result:
            response_log(f"No active price found for item {item_no} ({uom})", NOT_FOUND, True)
            return marshal_response_msg({
                "error_message" : "Not Found",
                "error_details" : "No active price found for item",
                "error_code" : NOT_FOUND,
                "is_error" : True
            })

        base_price = result.get("sales_price") or 0

        final_data = {
            "rate": base_price,
            "base_price": base_price,
            "sales_price": base_price,
            "discount_value": 0,
            "applied_discount": 0,
            "discount_type": " ",
            "discount_priority": None,
            "price_priority": matched_priority,
            "lower_limit": result.get("lower_limit"),
            "upper_limit": result.get("upper_limit"),
            "modified_date": result.get("updated"),
            "name": str(result.get("id", "")),
        }

        response_log("Get price priority completed", SUCCESS, False)

        return marshal_response_msg({
            "data" : final_data,
            "success_message" : "Successfully selected price priority",
            "success_code" : SUCCESS,
            "source" : SOURCE,
            "is_error" : False
        })

    except ConnectionError as e:
        response_log("Databse connection error, unable to connect database", SERVICE_UNAVAILABLE, True, str(e))
        return marshal_response_msg({
            "error_message" : "Databse connection error, unable to connect database",
            "error_details" : str(e),
            "error_code" : SERVICE_UNAVAILABLE,
            "is_error" : True
        })
    except pymysql.MySQLError as e:
        response_log("Database error while fetching prices priority", INTERNAL_SERVER_ERROR, True, str(e))
        return marshal_response_msg({
            "error_message" : "Database error while fetching prices priority",
            "error_details" : str(e),
            "error_code" : INTERNAL_SERVER_ERROR,
            "is_error" : True
        })
    except Exception as e:
        response_log("Unexpected error while fetching prices priority data", NOT_IMPLEMENTED, True, str(e))
        return marshal_response_msg({
            "error_message" : "Unexpected error while fetching prices priority data",
            "error_details" : str(e),
            "error_code" : NOT_IMPLEMENTED,
            "is_error" : True
        })

    finally:
        if cursor:
            cursor.close()
        if con:
            con.close()
