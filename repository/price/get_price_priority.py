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
        item_no = _val(data, "item_no")
        uom = _val(data, "unit_of_measure_code")

        context = (
            f"Price lookup item={item_no} "
            f"uom={uom} qty={data.get('qty')}"
        )

        if not item_no or not uom:
            response_log("item_no and unit_of_measure_code are required", BAD_REQUEST, True)
            return ("", {"error" : True, "error_code" : BAD_REQUEST})

        try:
            quantity = float(_val(data, "qty") or 1)
        except (ValueError, TypeError):
            response_log("Quanty must be a number", BAD_REQUEST, True)
            return ("", {"error" : True, "error_code" : BAD_REQUEST})

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
            return ("", {"error" : True, "error_code" : NOT_FOUND})

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

        return (final_data, {"error" : False, "error_code" : SUCCESS})

    except ConnectionError as e:
        mysql_error_code = e.args[0] if e.args else None
        http_status = SERVICE_UNAVAILABLE if mysql_error_code in (2002, 2003, 2006, 2013) else INTERNAL_SERVER_ERROR

        response_log("Databse connection error, unable to connect database", http_status, True, str(e))

        return ("", {
            "error" : True, 
            "error_code" : http_status})
    
    except pymysql.MySQLError as e:
        mysql_error_code = e.args[0] if e.args else None
        http_status = SERVICE_UNAVAILABLE if mysql_error_code in (2002, 2003, 2006, 2013) else INTERNAL_SERVER_ERROR

        response_log("Database error while fetch all log message", http_status, True, str(e))
        
        return ("", {
            "error" : True, 
            "error_code" : http_status})
    
    except Exception as e:
        response_log("Unexpected error while fetch all log message", NOT_IMPLEMENTED, True, str(e))
        
        return ("", {
            "error" : True, 
            "error_code" : NOT_IMPLEMENTED})

    finally:
        if cursor:
            cursor.close()
        if con:
            con.close()
