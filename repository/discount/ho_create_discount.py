import os
import re
import time
from decimal import Decimal, InvalidOperation
from datetime import datetime, date

import pymysql
from flask import jsonify

from repository.mysql_connection import get_db_connection
from utils.log_error import logger
from utils.file_path import upload_price_directory
from repository.query import (
    insert_discount_query,
    deactivate_discount_combination_query,
    insert_discount_version_query,
)
from repository.discount.write_lock import discount_write_lock
from data.structure.deactivation_combination import COMBINATION_COLUMNS as combination


DISCOUNT_DB = os.getenv("DB_D_NAME")

# changed record, lock wait timeout, deadlock
RETRYABLE_ERRORS = {1020, 1205, 1213}

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


def _to_datetime(value):
    if isinstance(value, datetime):
        return value
    if isinstance(value, date):
        return datetime.combine(value, datetime.min.time())
    s = str(value).strip()
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d",
                "%d-%m-%Y %H:%M:%S", "%d-%m-%Y", "%d/%m/%Y %H:%M:%S", "%d/%m/%Y"):
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            continue
    raise ValueError(f"invalid starting_date: {value!r}")


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


def ho_create_discount(records, file, invalid_data):
    """Public entry point: retries the whole upload when MariaDB reports a conflict."""
    for attempt in range(3):
        try:
            return _ho_create_discount_once(records, file, invalid_data)
        except pymysql.err.OperationalError as e:
            if e.args[0] not in RETRYABLE_ERRORS or attempt == 2:
                raise
            logger.warning("Discount upload conflict (%s), retrying", e.args[0])
            time.sleep(0.2 * (attempt + 1))


def _ho_create_discount_once(records, file, invalid_data):
    con = None
    cursor = None
    current = None

    if invalid_data is None:
        invalid_data = []

    try:
        con = get_db_connection(DISCOUNT_DB)
        cursor = con.cursor()

        inserted = 0
        deactivated = 0
        skipped = []   # records that failed validation inside the lock

        # The whole upload is one transaction under the shared lock,
        # so single saves and the scheduler cannot interleave with it.
        with discount_write_lock(cursor):
            # 1. Version row first; the database assigns the id
            version_sql, version_params = insert_discount_version_query({
                "id": None,
                "file_name": file.filename if file else "",
                "record_count": 0,
            })
            cursor.execute(version_sql, version_params)
            version_id = cursor.lastrowid

            now = datetime.now()
            for data in records:
                current = data

                if not isinstance(data, dict) or not data.get("item_no"):
                    logger.warning("Skipping record without item_no: %r", data)
                    continue

                # 0. validate BEFORE touching the DB, so a bad row never deactivates a good discount
                original = dict(data)
                try:
                    _clean_record(data)
                    is_future = _to_datetime(data.get("starting_date")) > now
                except ValueError as e:
                    logger.warning("Invalid record item_no=%s: %s", data.get("item_no"), e)
                    invalid_data.append({**original, "reason": str(e)})
                    continue

                # 1. old discounts for this combination -> inactive (only if the new one has started)
                if not is_future:
                    deact_sql, deact_params = deactivate_discount_combination_query(data, combination=combination)
                    cursor.execute(deact_sql, deact_params)
                    deactivated += cursor.rowcount

                # 2. new discount -> active only if it has started
                data["active"] = 0 if is_future else 1
                data["version_id"] = version_id

                sql_query, params = insert_discount_query(data)
                try:
                    cursor.execute(sql_query, params)
                except pymysql.err.DataError:
                    logger.error("Insert failed for item_no=%s SQL: %s",
                                 data.get("item_no"), cursor.mogrify(sql_query, params))
                    raise
                inserted += 1

            current = None

            # 3. Record the real count on the version row
            cursor.execute(
                "UPDATE DISCOUNT_VERSION SET record_count = %s WHERE id = %s",
                (inserted, version_id),
            )

            if file:
                file_path = os.path.join(upload_price_directory, file.filename)
                file.save(file_path)

            con.commit()   # deactivations, inserts and version land together

        return jsonify({
            "status": "success",
            "message": f"{inserted} discount(s) inserted, {deactivated} old discount(s) deactivated",
            "count": inserted,
            "deactivated": deactivated,
            "InvalidData": invalid_data
        }), 201

    except pymysql.MySQLError as e:
        if con:
            con.rollback()
        # Conflict errors go back to the retry wrapper
        if isinstance(e, pymysql.err.OperationalError) and e.args[0] in RETRYABLE_ERRORS:
            raise
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

    except ConnectionError as e:
        if con:
            con.rollback()
        logger.error(f"Database connection error: {e}")
        return jsonify({
            "status": "error",
            "message": "Unable to connect to database",
            "error": str(e)
        }), 503

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