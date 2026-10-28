from flask import jsonify, request
from repository.mysql_connection import get_db_connection
from utils.log_error import logger
import pymysql
from utils.log_response import _respond
import os
from data.error_codes import (
    INITIATING_FUNCTION,
    BAD_REQUEST,
    SUCCESS,
    SERVICE_UNAVAILABLE,
    INTERNAL_SERVER_ERROR,
    NOT_FOUND
)

LOG_SOURCE = "price_priority"

# Payload key -> PRICING_TABLE column
FIELD_MAP = {
    "customer_no":               "customer",
    "customer_group":            "customer_grp",
    "customer_hierarchy":        "customer_hierarchy",
    "distribution_channel_code": "distribution_channel_code",
    "location_code":             "location_code",
    "transportation_zone_code":  "transportation_zone_code",
}


# Access sequence: priority -> key columns (item_no + uom are always required)
PRIORITY_RULES = [
    (1,  ["distribution_channel_code", "customer", "location_code"]),
    (2,  ["distribution_channel_code", "customer_grp", "location_code"]),
    (3,  ["distribution_channel_code", "customer"]),
    (4,  ["distribution_channel_code", "customer_grp"]),
    (5,  ["customer_grp"]),
    (6,  ["customer_hierarchy", "location_code"]),
    (7,  ["customer_hierarchy"]),
    (8,  ["distribution_channel_code", "location_code", "transportation_zone_code"]),
    (9,  ["distribution_channel_code", "location_code"]),
    (10, ["distribution_channel_code"]),
    (11, []),
]


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

def _price_query(key_columns):
    where = "".join(f" AND {col} = %s" for col in key_columns)
    return (
        "SELECT * FROM PRICING_TABLE"
        " WHERE active = 1"
        "   AND priority = %s"
        "   AND item_no = %s"
        "   AND uom = %s"
        "   AND COALESCE(minimum_quantity, 0) <= %s"
        "   AND ending_date >= NOW()"
        f"{where}"
        " ORDER BY (starting_date <= NOW()) DESC,"
        "          minimum_quantity DESC,"
        "          starting_date DESC"
        " LIMIT 1"
    )

def get_price_priority(data):
    con = None
    cursor = None
    log_type = "Get Price Priority"
    ipaddress = request.remote_addr

    _respond(
        body={},
        custom_message="Entered in getprice priority function",
        ipaddress=ipaddress,
        response_message="",
        source=LOG_SOURCE,
        log_type=log_type,
        message_code=f"PP{INITIATING_FUNCTION}",
        log_status=INITIATING_FUNCTION,
        error=False
    )
    try:
        if not data or not isinstance(data, dict):
            return _respond(
                body={
                    "status": "error",
                    "message": "Request data is empty or invalid"
                },
                log_type=log_type,
                log_status=BAD_REQUEST,
                custom_message="Request data is empty or invalid",
                message_code=f"PP{BAD_REQUEST}",
                error=True,
                response_message="",
                ipaddress=ipaddress,
                source=LOG_SOURCE
            )

        item_no = _val(data, "item_no")
        uom = _val(data, "unit_of_measure_code")

        context = (
            f"Price lookup item={item_no} "
            f"uom={uom} qty={data.get('qty')}"
        )

        if not item_no or not uom:
            return _respond(
                body={
                    "status": "error",
                    "message": (
                        "item_no and unit_of_measure_code are required"
                    )
                },
                log_type=log_type,
                log_status=BAD_REQUEST,
                custom_message="item_no and unit_of_measure_code are required",
                message_code=f"PP{BAD_REQUEST}",
                error=True,
                response_message="",
                source=LOG_SOURCE,
                ipaddress=ipaddress
            )

        try:
            quantity = float(_val(data, "qty") or 1)
        except (ValueError, TypeError):
            return _respond(
                body={
                    "status": "error",
                    "message": "qty must be a number"
                },
                log_type=log_type,
                log_status=BAD_REQUEST,
                custom_message="qty must be a number",
                message_code=f"PP{BAD_REQUEST}",
                error=True,
                response_message="",
                source=LOG_SOURCE,
                ipaddress=ipaddress
            )

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
            return _respond(
                body={
                    "status": "error",
                    "message": (
                        f"No active price found for item {item_no} ({uom})"
                    ),
                    "checked_priorities": checked
                },
                log_type=log_type,
                log_status=NOT_FOUND,
                custom_message=(
                    f"No active price found, checked priorities {checked}"
                ),
                message_code=f"PP{NOT_FOUND}",
                error=True,
                response_message="",
                source=LOG_SOURCE,
                ipaddress=ipaddress
            )

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

        return _respond(
            body={
                "data": "Item price with discount applied",
                "message": final_data
            },
            log_type=log_type,
            log_status=SUCCESS,
            custom_message=(
                f"Price {base_price} found at priority "
                f"{matched_priority} (id {result.get('id')})"
            ),
            message_code=f"PP{SUCCESS}",
            error=False,
            response_message="",
            source=LOG_SOURCE,
            ipaddress=ipaddress
        )

    except ConnectionError as e:
        logger.exception(
            "Database connection error while fetching price priority"
        )

        return _respond(
            body={
                "status": "error",
                "message": "Unable to connect to database",
                "error": str(e)
            },
            log_type=log_type,
            log_status=SERVICE_UNAVAILABLE,
            custom_message="Unable to connect to database",
            message_code=f"PP{SERVICE_UNAVAILABLE}",
            error=True,
            response_message=str(e),
            source=LOG_SOURCE,
            ipaddress=ipaddress
        )

    except pymysql.MySQLError as e:
        logger.exception(
            "Database error while fetching price priority"
        )

        return _respond(
            body={
                "status": "error",
                "message": "Database error",
                "error": str(e)
            },
            log_type=log_type,
            log_status=INTERNAL_SERVER_ERROR,
            custom_message="Database error",
            message_code=f"PP{INTERNAL_SERVER_ERROR}",
            error=True,
            response_message=str(e),
            source=LOG_SOURCE,
            ipaddress=ipaddress
        )

    except Exception as e:
        logger.exception(
            "Unexpected error while fetching price priority"
        )

        return _respond(
            body={
                "status": "error",
                "message": "Something went wrong",
                "error": str(e)
            },
            log_type=log_type,
            log_status=INTERNAL_SERVER_ERROR,
            custom_message="Something went wrong",
            message_code=f"PP{INTERNAL_SERVER_ERROR}",
            error=True,
            response_message=str(e),
            source=LOG_SOURCE,
            ipaddress=ipaddress
        )

    finally:
        if cursor:
            cursor.close()
        if con:
            con.close()
