from flask import jsonify, request
from repository.query import create_logger
from repository.mysql_connection import get_db_connection
from utils.log_error import logger
from repository.price.create_log import write_log
import pymysql
import os

LOG_SOURCE = "price_priority"
LOG_TYPE = "PRICE_FETCH"

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
        "   AND NOW() BETWEEN starting_date AND ending_date"
        f"{where}"
        " ORDER BY minimum_quantity DESC, starting_date DESC"
        " LIMIT 1"
    )


def _respond(body, status, context, message_code, is_error, response_message=None):
    """Write the log row, then return the JSON response."""
    write_log(
        custom_message=context,
        response_message=response_message or body.get("message"),
        source=LOG_SOURCE,
        log_type=LOG_TYPE,
        message_code=message_code,
        log_status=status,
        info=not is_error,
        error=is_error,
    )
    return jsonify(body), status


def get_price_priority(data):
    con = None
    cursor = None
    context = "Price lookup"

    try:
        if not data or not isinstance(data, dict):
            return _respond(
                {"status": "error", "message": "Request data is empty or invalid"},
                400, context, "PP400", True
            )

        item_no = _val(data, "item_no")
        uom = _val(data, "unit_of_measure_code")
        context = f"Price lookup item={item_no} uom={uom} qty={data.get('qty')}"

        if not item_no or not uom:
            return _respond(
                {"status": "error", "message": "item_no and unit_of_measure_code are required"},
                400, context, "PP400", True
            )

        try:
            quantity = float(_val(data, "qty") or 1)
        except ValueError:
            return _respond(
                {"status": "error", "message": "qty must be a number"},
                400, context, "PP400", True
            )

        # Values the caller provided, keyed by DB column
        provided = {col: _key_val(data, key) for key, col in FIELD_MAP.items()}

        con = get_db_connection(os.getenv("DB_P_NAME"))
        cursor = con.cursor()

        result = None
        matched_priority = None
        checked = []

        for priority, key_columns in PRIORITY_RULES:

            # Skip priorities whose key fields weren't supplied
            if any(provided[col] is None for col in key_columns):
                continue

            checked.append(priority)

            params = [priority, item_no, uom, quantity] + [provided[col] for col in key_columns]
            cursor.execute(_price_query(key_columns), params)
            row = cursor.fetchone()

            if row:
                result = row
                matched_priority = priority
                break

        logger_sql_query, logger_params = create_logger(
            request.remote_addr, "Fetching item pricing priority"
        )
        cursor.execute(logger_sql_query, logger_params)
        con.commit()

        if not result:
            return _respond(
                {
                    "status": "error",
                    "message": f"No active price found for item {item_no} ({uom})",
                    "checked_priorities": checked
                },
                404, context, "PP404", False,
                response_message=f"No active price found, checked priorities {checked}"
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
            {"data": "Item price with discount applied", "message": final_data},
            200, context, "PP200", False,
            response_message=f"Price {base_price} found at priority {matched_priority} (id {result.get('id')})"
        )

    except ConnectionError as e:
        logger.exception("Database connection error while fetching price priority")
        return _respond(
            {"status": "error", "message": "Unable to connect to database", "error": str(e)},
            503, context, "PP503", True, response_message=str(e)
        )

    except pymysql.MySQLError as e:
        if con:
            con.rollback()
        logger.exception("Database error while fetching price priority")
        return _respond(
            {"status": "error", "message": "Database error", "error": str(e)},
            500, context, "PP500", True, response_message=str(e)
        )

    except Exception as e:
        if con:
            con.rollback()
        logger.exception("Unexpected error while fetching price priority")
        return _respond(
            {"status": "error", "message": "Something went wrong", "error": str(e)},
            500, context, "PP501", True, response_message=str(e)
        )

    finally:
        if cursor:
            cursor.close()
        if con:
            con.close()