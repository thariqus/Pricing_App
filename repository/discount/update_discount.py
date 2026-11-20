import os
import time

import pymysql
from flask import jsonify

from repository.mysql_connection import get_db_connection
from utils.log_error import logger
from repository.query import (
    check_discount_exists,
    update_discount,
    insert_discount_version_query,
)
from repository.discount.write_lock import discount_write_lock

DISCOUNT_DB = os.getenv("DB_D_NAME")

# changed record, lock wait timeout, deadlock
RETRYABLE_ERRORS = {1020, 1205, 1213}


def update_discount_data(data):
    """Public entry point: retries the whole update when MariaDB reports a conflict."""
    for attempt in range(3):
        try:
            return _update_discount_data_once(data)
        except pymysql.err.OperationalError as e:
            if e.args[0] not in RETRYABLE_ERRORS or attempt == 2:
                return _error_response(e, 500, "Database error")
            logger.warning("Discount update conflict (%s), retrying", e.args[0])
            time.sleep(0.2 * (attempt + 1))


def _update_discount_data_once(data):
    con = None
    cursor = None
    try:
        con = get_db_connection(DISCOUNT_DB)
        cursor = con.cursor()

        failed_records = []
        valid_updates = []   # (discount_id, changes) that passed every check

        # Validate and write under the same lock, so a row can't change or
        # disappear between the check and the update.
        with discount_write_lock(cursor):
            for record in data:
                discount_id = record.get("id")
                if not discount_id:
                    failed_records.append({
                        "data": record,
                        "message": "Discount ID is required"
                    })
                    continue

                cursor.execute(*check_discount_exists(discount_id))
                if not cursor.fetchone():
                    failed_records.append({
                        "id": discount_id,
                        "message": "Discount record not found"
                    })
                    continue

                changes = {
                    key: value
                    for key, value in record.items()
                    if key not in ("id", "version_id")   # the server sets the version
                }
                if not changes:
                    failed_records.append({
                        "id": discount_id,
                        "message": "No fields to update"
                    })
                    continue

                valid_updates.append((discount_id, changes))

            new_version = None
            updated_records = []

            # One new version for the whole request, only if something changed
            if valid_updates:
                version_sql, version_params = insert_discount_version_query({
                    "id": None,
                    "file_name": "update",
                    "record_count": len(valid_updates),
                })
                cursor.execute(version_sql, version_params)
                new_version = cursor.lastrowid

                for discount_id, changes in valid_updates:
                    changes["version_id"] = new_version
                    sql_query, params = update_discount(discount_id, changes)
                    cursor.execute(sql_query, params)
                    updated_records.append({
                        "id": discount_id,
                        "version_id": new_version
                    })

            con.commit()   # commit while the lock is still held

        return jsonify({
            "status": "success",
            "message": "Discount update completed",
            "version_id": new_version,
            "updated_count": len(updated_records),
            "updated": updated_records,
            "failed_count": len(failed_records),
            "failed": failed_records
        }), 200

    except pymysql.MySQLError as e:
        if con:
            con.rollback()
        if isinstance(e, pymysql.err.OperationalError) and e.args[0] in RETRYABLE_ERRORS:
            raise   # the wrapper runs the update again
        logger.exception("Database error while updating discount")
        return _error_response(e, 500, "Database error")

    except ConnectionError as e:
        if con:
            con.rollback()
        logger.error(f"Database connection error: {e}")
        return _error_response(e, 503, "Unable to connect to database")

    except Exception as e:
        if con:
            con.rollback()
        logger.exception("Unexpected error while updating discount")
        return _error_response(e, 500, "Something went wrong")

    finally:
        if cursor:
            cursor.close()
        if con:
            con.close()


def _error_response(error, status, message):
    return jsonify({
        "status": "error",
        "message": message,
        "error": str(error)
    }), status