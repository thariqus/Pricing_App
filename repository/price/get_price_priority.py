from flask import jsonify, request
from repository.query import create_logger
from repository.mysql_connection import get_db_connection
from utils.log_error import logger
import pymysql
import os

PRICE_DB = os.getenv("DB_P_NAME")

# Payload key -> PRICING_TABLE column
FIELD_MAP = {
    "Customer_No":               "customer",
    "Customer_Group":            "customer_grp",
    "Customer_Hierarchy":        "customer_hierarchy",
    "Distribution_Channel_Code": "distribution_channel_code",
    "Location_Code":             "location_code",
    "Transportation_Zone_Code":  "transportation_zone_code",
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


def get_price_priority(data):
    con = None
    cursor = None
    try:
        if not data:
            return jsonify({"status": "error", "message": "Request data is empty"}), 400

        item_no = _val(data, "Item_No")
        uom = _val(data, "uom")

        if not item_no or not uom:
            return jsonify({"status": "error", "message": "Item_No and uom are required"}), 400

        try:
            quantity = float(_val(data, "Quantity") or 1)
        except ValueError:
            return jsonify({"status": "error", "message": "Quantity must be a number"}), 400

        # Values the caller provided, keyed by DB column
        provided = {col: _val(data, key) for key, col in FIELD_MAP.items()}

        con = get_db_connection(PRICE_DB)
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
            return jsonify({
                "status": "error",
                "message": f"No active price found for item {item_no} ({uom})",
                "checked_priorities": checked
            }), 404

        return jsonify({
            "status": "Success",
            "priority": matched_priority,
            "checked_priorities": checked,
            "data": result
        }), 200

    except pymysql.MySQLError as e:
        if con:
            con.rollback()
        logger.exception("Database error while fetching price priority")
        return jsonify({"status": "error", "message": "Database error", "error": str(e)}), 500

    except Exception as e:
        if con:
            con.rollback()
        logger.exception("Unexpected error while fetching price priority")
        return jsonify({"status": "error", "message": "Something went wrong", "error": str(e)}), 500

    finally:
        if cursor:
            cursor.close()
        if con:
            con.close()