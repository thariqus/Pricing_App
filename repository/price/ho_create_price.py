import os
from flask import request
from repository.mysql_connection import get_db_connection
from utils.file_path import upload_price_directory
from repository.query import (
    insert_price_query,
    deactivate_combination_query,
    get_latest_version_id_query,   # version
    insert_version_query,          # version
)

from data.structure.deactivation_combination import COMBINATION_COLUMNS as combination
import pymysql
from datetime import datetime
from data.data_processing._clean_record import _clean_record
from data.data_processing._to_datetime import _to_datetime
from utils.log_response import _respond
from data.error_codes import INITIATING_FUNCTION, SUCCESS, SERVICE_UNAVAILABLE, INTERNAL_SERVER_ERROR, BAD_REQUEST, CREATED, NOT_IMPLEMENTED
from data.response import marshal_response_msg

PRICE_DB = os.getenv("DB_P_NAME")
SOURCE = "/api/items/store_csv_uploads"

def response_log(custom_message, code, error, response_message=None):
    return _respond(
        body={},
        custom_message=custom_message,
        ipaddress=request.remote_addr,
        response_message=response_message,
        source="repository",
        log_type="Create HO price",
        message_code=f"PP{code}",
        log_status=code,
        error=error
    )

def ho_create_price(records, file, invalid_data):
    con = None
    cursor = None
    current = None
    response_log("Enter into get ho price create function", INITIATING_FUNCTION, False)

    if invalid_data is None:
        invalid_data = []
        
    try:
        if not records:
            response_log("No records found", BAD_REQUEST, True)
            return marshal_response_msg({
                "error_message" : "Not found",
                "error_details" : "Records is required, but not given",
                "error_code" : BAD_REQUEST,
                "is_error" : True
            })

        con = get_db_connection(PRICE_DB)
        cursor = con.cursor()

        inserted = 0
        deactivated = 0

        cursor.execute(get_latest_version_id_query())
        row = cursor.fetchone()
        latest = (row["version_id"] if isinstance(row, dict) else row[0]) if row else None
        version_id = (latest or 0) + 1

        now = datetime.now()

        for data in records:
            current = data

            if not isinstance(data, dict) or not data.get("item_no"):
                continue

            # 0. validate BEFORE touching the DB, so a bad row never deactivates a good price
            original = dict(data)
            try:
                _clean_record(data)
                is_future = _to_datetime(data.get("starting_date")) > now
            except ValueError as e:
                invalid_data.append({**original, "reason": str(e)})
                continue

            # 1. old prices for this combination -> inactive (only if the new price has started)
            if not is_future:
                deact_sql, deact_params = deactivate_combination_query(data, combination=combination)
                cursor.execute(deact_sql, deact_params)
                deactivated += cursor.rowcount

            # 2. new price -> active only if it has started
            data["active"] = 0 if is_future else 1
            data["version_id"] = version_id   # version

            sql_query, params = insert_price_query(data)
            try:
                cursor.execute(sql_query, params)
            except pymysql.err.DataError:
                raise
            inserted += 1

        current = None

        if inserted:
            response_log("HO price inserted complete", SUCCESS, False)
            version_sql, version_params = insert_version_query({
                "id": version_id,
                "file_name": file.filename if file else "",
                "record_count": inserted,
            })
            cursor.execute(version_sql, version_params)

        if file:
            file_path = os.path.join(upload_price_directory, file.filename)
            file.save(file_path)

        con.commit()   # deactivations + inserts land together

        response_log("HO price insert completed", SUCCESS, False)
        return marshal_response_msg({
            "success_message" : f"{inserted} price(s) inserted, {deactivated} old price(s) deactivated",
            "success_code" : CREATED,
            "source" : SOURCE,
            "is_error" : False,
            "custom_field" : {
                "count": inserted,
                "deactivated": deactivated,
                "InvalidData": invalid_data
            }
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
        response_log("Database error while fetching ho create prices", INTERNAL_SERVER_ERROR, True, str(e))
        return marshal_response_msg({
            "error_message" : "Database error while fetching ho create prices",
            "error_details" : str(e),
            "error_code" : INTERNAL_SERVER_ERROR,
            "is_error" : True
        })
    except Exception as e:
        response_log("Unexpected error while fetching ho create price data", NOT_IMPLEMENTED, True, str(e))
        return marshal_response_msg({
            "error_message" : "Unexpected error while fetching ho create price data",
            "error_details" : str(e),
            "error_code" : NOT_IMPLEMENTED,
            "is_error" : True
        })

    finally:
        if cursor:
            cursor.close()
        if con:
            con.close()