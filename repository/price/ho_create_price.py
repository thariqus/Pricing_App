import os
import re
from decimal import Decimal, InvalidOperation
from flask import jsonify, request
from repository.mysql_connection import get_db_connection
from utils.log_error import logger
from utils.file_path import upload_price_directory
from repository.query import insert_price_query, deactivate_combination_query, create_logger
from data.structure.deactivation_combination import COMBINATION_COLUMNS as combination
import pymysql


PRICE_DB = os.getenv("DB_P_NAME")

REQUIRED_NUMERIC = ("sales_price",)
OPTIONAL_NUMERIC = ("lower_limit", "upper_limit", "minimum_quantity")

# Key fields as they appear in the parsed CSV record
KEY_FIELDS = (
    "customer_no",
    "customer_group",
    "customer_hierarchy",
    "distribution_channel_code",
    "location_code",
    "transportation_zone_code",
)

# Access sequence: priority -> key fields that must be filled (item_no + uom always required)
PRIORITY_RULES = {
    1:  ("distribution_channel_code", "customer_no", "location_code"),
    2:  ("distribution_channel_code", "customer_group", "location_code"),
    3:  ("distribution_channel_code", "customer_no"),
    4:  ("distribution_channel_code", "customer_group"),
    5:  ("customer_group",),
    6:  ("customer_hierarchy", "location_code"),
    7:  ("customer_hierarchy",),
    8:  ("distribution_channel_code", "location_code", "transportation_zone_code"),
    9:  ("distribution_channel_code", "location_code"),
    10: ("distribution_channel_code",),
    11: (),
}


def _is_blank(value):
    if value is None:
        return True
    if isinstance(value, float) and value != value:   # NaN
        return True
    return str(value).strip().lower() in ("", "nan", "none", "null")


def _to_number(value):
    """Return Decimal, or None for empty values. Raise ValueError for garbage."""
    if value is None:
        return None
    if isinstance(value, float):
        return None if value != value else Decimal(str(value))   # NaN check
    if isinstance(value, (int, Decimal)):
        return Decimal(value)
    s = str(value).strip().replace(",", "")
    if s == "" or s.lower() in ("nan", "none", "null"):
        return None
    try:
        return Decimal(s)
    except InvalidOperation:
        raise ValueError(f"not a number: {value!r}")


def _check_priority(data):
    # 1. priority must be a whole number 1-11
    raw = data.get("priority")
    if _is_blank(raw):
        raise ValueError("priority is empty")
    try:
        num = Decimal(str(raw).strip())
    except InvalidOperation:
        raise ValueError(f"priority is not a number: {raw!r}")
    if num != num.to_integral_value() or int(num) not in PRIORITY_RULES:
        raise ValueError(f"priority must be 1 to {len(PRIORITY_RULES)}, got {raw!r}")
    priority = int(num)
    data["priority"] = priority

    # 2. item_no and uom are always required
    for field in ("item_no", "uom"):
        if _is_blank(data.get(field)):
            raise ValueError(f"{field} is required")

    # 3. key fields for this priority must be filled
    required = PRIORITY_RULES[priority]
    missing = [f for f in required if _is_blank(data.get(f))]
    if missing:
        raise ValueError(
            f"priority {priority} requires {', '.join(required)} "
            f"(missing: {', '.join(missing)})"
        )

    # 4. key fields NOT used by this priority must be empty
    extra = [f"{f}={data.get(f)!r}" for f in KEY_FIELDS
             if f not in required and not _is_blank(data.get(f))]
    if extra:
        raise ValueError(
            f"priority {priority} must not have {', '.join(extra)} "
            f"(leave these empty or use a different priority)"
        )


def _clean_record(data):
    for field in REQUIRED_NUMERIC:
        try:
            num = _to_number(data.get(field))
        except ValueError as e:
            raise ValueError(f"{field} {e}")
        if num is None:
            raise ValueError(f"{field} is empty")
        data[field] = num
    for field in OPTIONAL_NUMERIC:
        if field in data:
            try:
                data[field] = _to_number(data[field])
            except ValueError as e:
                raise ValueError(f"{field} {e}")

    _check_priority(data)


def ho_create_price(records, file, invalid_data):
    con = None
    cursor = None
    current = None
    try:
        con = get_db_connection(PRICE_DB)
        cursor = con.cursor()

        inserted = 0
        deactivated = 0

        for data in records:
            current = data

            if not isinstance(data, dict) or not data.get("item_no"):
                logger.warning("Skipping record without item_no: %r", data)
                continue

            # 0. validate BEFORE touching the DB, so a bad row never deactivates a good price
            original = dict(data)
            try:
                _clean_record(data)
            except ValueError as e:
                logger.warning("Invalid record item_no=%s: %s", data.get("item_no"), e)
                invalid_data.append({**original, "reason": str(e)})
                continue

            # 1. old prices for this combination -> inactive
            deact_sql, deact_params = deactivate_combination_query(data, combination=combination)
            cursor.execute(deact_sql, deact_params)
            deactivated += cursor.rowcount

            # 2. new price -> active
            data["active"] = 1
            sql_query, params = insert_price_query(data)
            try:
                cursor.execute(sql_query, params)
            except pymysql.err.DataError:
                logger.error("Insert failed for item_no=%s SQL: %s",
                             data.get("item_no"), cursor.mogrify(sql_query, params))
                raise
            inserted += 1

        current = None   # loop finished; errors after this aren't tied to a row

        if file:
            file_path = os.path.join(upload_price_directory, file.filename)
            file.save(file_path)

            logger_sql_query, logger_params = create_logger(
                request.remote_addr, "Insert Item Price CSV Data", file_path
            )
            cursor.execute(logger_sql_query, logger_params)

        con.commit()   # deactivations + inserts land together

        return jsonify({
            "status": "success",
            "message": f"{inserted} price(s) inserted, {deactivated} old price(s) deactivated",
            "count": inserted,
            "deactivated": deactivated,
            "InvalidData": invalid_data
        }), 201

    except ConnectionError as e:
        logger.error(f"Database connection error: {e}")
        return jsonify({
            "status": "error",
            "message": "Unable to connect to database",
            "error": str(e)
        }), 503

    except pymysql.MySQLError as e:
        if con:
            con.rollback()
        logger.exception("Database error while inserting CSV data")

        failed = None
        message = "Database error while inserting CSV data. Please check the file."

        if current:
            m = re.search(r"column '(\w+)'", str(e))
            column = m.group(1) if m else None
            value = current.get(column) if column else None
            failed = {
                "item_no": current.get("item_no"),
                "uom": current.get("uom"),
                "column": column,
                "value": None if value is None else str(value),
            }
            if column:
                message = (f"Item {failed['item_no']} ({failed['uom']}): "
                           f"invalid value '{failed['value']}' in column '{column}'. "
                           "Nothing was imported — fix this row and upload again.")
            else:
                message = (f"Database error on item {failed['item_no']} ({failed['uom']}). "
                           "Nothing was imported — please check this row.")

        status = 400 if isinstance(e, pymysql.err.DataError) else 500
        return jsonify({
            "status": "error",
            "message": message,
            "error": str(e),
            "failed_record": failed
        }), status

    except Exception as e:
        if con:
            con.rollback()
        logger.exception("Unexpected error while inserting CSV data")
        return jsonify({
            "status": "error",
            "message": "Something went wrong",
            "error": str(e)
        }), 500

    finally:
        if cursor:
            cursor.close()
        if con:
            con.close()