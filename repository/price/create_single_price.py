from flask import request, jsonify
import pymysql
from repository.mysql_connection import get_db_connection
from utils.log_error import logger
from repository.query import insert_price_query, get_latest_version_id_query, insert_version_query  
from repository.price.create_log import write_log
from data.error_codes import (
    INITIATING_FUNCTION,
    BAD_REQUEST,
    SUCCESS,
    SERVICE_UNAVAILABLE,
    INTERNAL_SERVER_ERROR,
    NOT_IMPLEMENTED
)
import os

LOG_SOURCE = "repository"

PRICE_DB = os.getenv("DB_P_NAME")

def _respond(body, ipaddress, log_type, status, context, message_code, is_error, response_message=None):
    """Write the log row, then return the JSON response."""
    write_log(
        custom_message=context,
        response_message=response_message or body.get("message"),
        source=LOG_SOURCE,
        log_type=log_type,
        message_code=message_code,
        log_status=status,
        info=not is_error,
        error=is_error,
        ipaddress = ipaddress
    )
    return jsonify(body), status


def create_single_price(data):
    _respond(
        {},
        request.remote_addr,
        "Create Single Price",
        INITIATING_FUNCTION, 
        "Entered in single item price function",
        f"PP{INITIATING_FUNCTION}",
        False
    )
    con = None
    cursor = None
    context = "Single Item Price"
    try:
        if not data:
            return _respond(
                {"status": "error", "message": "Request data is empty or invalid"},
                request.remote_addr,
                "Create Single Price", BAD_REQUEST, context, f"PP{BAD_REQUEST}", True
            )
        con = get_db_connection(PRICE_DB)


        cursor = con.cursor()

        cursor.execute(get_latest_version_id_query())
        row = cursor.fetchone()
        latest = (row["version_id"] if isinstance(row, dict) else row[0]) if row else None
        version_id = (latest or 0) + 1
        data["version_id"] = version_id 


        sql_query, params = insert_price_query(data)
        cursor.execute(
            sql_query,
            params
        )
        inserted_id = cursor.lastrowid
        con.commit()

        if inserted_id:
            version_sql, version_params = insert_version_query({
                "id": version_id,
                "file_name": "",
                "record_count": 1,
            })
            cursor.execute(version_sql, version_params)
            con.commit()

            _respond(
                {},
                request.remote_addr,
                "Create Single Price",
                SUCCESS, 
                "Single Price Inserted",
                f"PP{SUCCESS}",
                False
            )

        _respond(
            {},
            request.remote_addr,
            "Create Single Price",
            SUCCESS,
            "Completed single item price",
            f"PP{SUCCESS}",
            False
        )

        return _respond(
            {"data": inserted_id },
            request.remote_addr,
            "Create Single Price", SUCCESS, context, f"PP{SUCCESS}", False,
            response_message = "Price created successfully"
        )
    
    except ConnectionError as e:
        logger.exception("Database connection error while creating price")
        return _respond(
            {
                "status": "error",
                "message": "Unable to connect to database",
                "error": str(e)
            },
            request.remote_addr,
            SERVICE_UNAVAILABLE, context, f"PC{SERVICE_UNAVAILABLE}", True, response_message=str(e)
        )

    except pymysql.MySQLError as e:
        if con:
            con.rollback()
        logger.exception("Database error while creating price")
        return _respond(
            {
                "status": "error",
                "message": "Database error",
                "error": str(e)
            },
            request.remote_addr,
            INTERNAL_SERVER_ERROR, context, f"PC{INTERNAL_SERVER_ERROR}", True, response_message=str(e)
        )

    except Exception as e:
        if con:
            con.rollback()
        logger.exception("Unexpected error while creating price")
        return _respond(
            {
                "status": "error",
                "message": "Something went wrong",
                "error": str(e)
            },
            request.remote_addr,
            NOT_IMPLEMENTED, context, f"PC{NOT_IMPLEMENTED}", True, response_message=str(e)
        )

    finally:
        if cursor:
            cursor.close()
        if con:
            con.close()