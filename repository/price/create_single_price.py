from flask import request
import pymysql
from repository.mysql_connection import get_db_connection
from utils.log_response import _respond
from repository.query import insert_price_query, get_latest_version_id_query, insert_version_query, deactivate_combination_query
from data.structure.deactivation_combination import COMBINATION_COLUMNS as combination
from data.error_codes import (
    INITIATING_FUNCTION,
    BAD_REQUEST,
    SUCCESS,
    SERVICE_UNAVAILABLE,
    INTERNAL_SERVER_ERROR,
    NOT_IMPLEMENTED,
    CREATED
)
import os
from datetime import datetime
from data.data_processing._clean_record import _clean_record
from data.data_processing._to_datetime import _to_datetime
from data.response import marshal_response_msg

SOURCE = "/api/items/create_singel_item_price"

PRICE_DB = os.getenv("DB_P_NAME")

def response_log(custom_message, code, error, response_message=None):
    return _respond(
        body={},
        custom_message=custom_message,
        ipaddress=request.remote_addr,
        response_message=response_message,
        source="repository",
        log_type="Create Single Price",
        message_code=f"PP{code}",
        log_status=code,
        error=error
    )

def create_single_price(data):
    con = None
    cursor = None

    # Log function entry
    response_log("Entered in single item price function", INITIATING_FUNCTION, False)

    try:
        print(data)
        if not data:
            response_log("Request data is empty or invalid", BAD_REQUEST, True)
            return marshal_response_msg({
                "error_message" : "Empty data given",
                "error_details" : "Given data is empty, please provide valid input",
                "error_code" : BAD_REQUEST,
                "is_error" : True
            })

        con = get_db_connection(PRICE_DB)
        cursor = con.cursor()

        cursor.execute(get_latest_version_id_query())
        row = cursor.fetchone()

        latest = (
            row["version_id"] if isinstance(row, dict) else row[0]
        ) if row else None

        version_id = (latest or 0) + 1

        try:
            _clean_record(data)
            is_future = _to_datetime(data.get("starting_date")) > datetime.now()
        except ValueError as e:
            return marshal_response_msg({
                "error_message" : "Invalid item",
                "error_details" : str(e),
                "error_code" : BAD_REQUEST,
                "is_error" : True
            })
    

        # 1. old prices for this combination -> inactive (only if the new price has started)
        if not is_future:
            deact_sql, deact_params = deactivate_combination_query(data, combination=combination)
            cursor.execute(deact_sql, deact_params)

        # 2. new price -> active only if it has started
        data["active"] = 0 if is_future else 1
        data["version_id"] = version_id

        sql_query, params = insert_price_query(data)
        cursor.execute(sql_query, params)
        inserted_id = cursor.lastrowid

        if not inserted_id:
            con.rollback()
            response_log("Price could not be created", INTERNAL_SERVER_ERROR, True)
            return marshal_response_msg({
                "error_message" : "Couldn't create",
                "error_details" : "Price couldn't be created",
                "error_code" : INTERNAL_SERVER_ERROR,
                "is_error" : True
            })

        version_sql, version_params = insert_version_query({
            "id": version_id,
            "file_name": "",
            "record_count": 1,
        })

        cursor.execute(version_sql, version_params)
        con.commit()

        response_log("Price created successfully", SUCCESS, False)

        return marshal_response_msg({
            "success_message" : f"{data.get("item_no")} is created successfully",
            "success_code" : CREATED,
            "source" : SOURCE,
            "is_error" : False
        })

    except ConnectionError as e:
        if con:
            con.rollback()
        response_log("Databse connection error, unable to connect database", SERVICE_UNAVAILABLE, True, str(e))
        return marshal_response_msg({
            "error_message" : "Databse connection error, unable to connect database",
            "error_details" : str(e),
            "error_code" : SERVICE_UNAVAILABLE,
            "is_error" : True
        })

    except pymysql.MySQLError as e:
        if con:
            con.rollback()
        response_log("Database error", INTERNAL_SERVER_ERROR, True, str(e))
        return marshal_response_msg({
            "error_message" : "Databse error",
            "error_details" : str(e),
            "error_code" : INTERNAL_SERVER_ERROR,
            "is_error" : True
        })

    except Exception as e:
        if con:
            con.rollback()
        response_log("Something went wrong", NOT_IMPLEMENTED, True, str(e))
        return marshal_response_msg({
            "error_message" : "Something went wrong",
            "error_details" : str(e),
            "error_code" : NOT_IMPLEMENTED,
            "is_error" : True
        })

    finally:
        if cursor:
            cursor.close()
        if con:
            con.close()
