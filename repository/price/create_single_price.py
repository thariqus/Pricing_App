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

def _respond(body, log_type, status, context, message_code, is_error, response_message=None, ipaddress=None):
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
    con = None
    cursor = None
    context = "Single Item Price"
    log_type = "Create Single Price"
    ipaddress = request.remote_addr

    # Log function entry
    write_log(
        custom_message="Entered in single item price function",
        ipaddress=ipaddress,
        response_message="",
        source=LOG_SOURCE,
        log_type=log_type,
        message_code=f"PP{INITIATING_FUNCTION}",
        log_status=INITIATING_FUNCTION,
        info=True,
        error=False
    )

    try:
        if not data:
            return _respond(
                body={
                    "status": "error",
                    "message": "Request data is empty or invalid"
                },
                log_type=log_type,
                status=BAD_REQUEST,
                context=context,
                message_code=f"PP{BAD_REQUEST}",
                is_error=True,
                response_message="Request data is empty or invalid",
                ipaddress=ipaddress
            )

        con = get_db_connection(PRICE_DB)
        cursor = con.cursor()

        cursor.execute(get_latest_version_id_query())
        row = cursor.fetchone()

        latest = (
            row["version_id"] if isinstance(row, dict) else row[0]
        ) if row else None

        version_id = (latest or 0) + 1
        data["version_id"] = version_id

        sql_query, params = insert_price_query(data)
        cursor.execute(sql_query, params)
        inserted_id = cursor.lastrowid

        if not inserted_id:
            con.rollback()
            return _respond(
                body={
                    "status": "error",
                    "message": "Price could not be created"
                },
                log_type=log_type,
                status=INTERNAL_SERVER_ERROR,
                context=context,
                message_code=f"PP{INTERNAL_SERVER_ERROR}",
                is_error=True,
                response_message="Price could not be created",
                ipaddress=ipaddress
            )

        version_sql, version_params = insert_version_query({
            "id": version_id,
            "file_name": "",
            "record_count": 1,
        })

        cursor.execute(version_sql, version_params)
        con.commit()

        return _respond(
            body={"data": inserted_id},
            log_type=log_type,
            status=SUCCESS,
            context=context,
            message_code=f"PP{SUCCESS}",
            is_error=False,
            response_message="Price created successfully",
            ipaddress=ipaddress
        )

    except ConnectionError as e:
        if con:
            con.rollback()

        logger.exception(
            "Database connection error while creating price"
        )

        return _respond(
            body={
                "status": "error",
                "message": "Unable to connect to database",
                "error": str(e)
            },
            log_type=log_type,
            status=SERVICE_UNAVAILABLE,
            context=context,
            message_code=f"PC{SERVICE_UNAVAILABLE}",
            is_error=True,
            response_message=str(e),
            ipaddress=ipaddress
        )

    except pymysql.MySQLError as e:
        if con:
            con.rollback()

        logger.exception(
            "Database error while creating price"
        )

        return _respond(
            body={
                "status": "error",
                "message": "Database error",
                "error": str(e)
            },
            log_type=log_type,
            status=INTERNAL_SERVER_ERROR,
            context=context,
            message_code=f"PC{INTERNAL_SERVER_ERROR}",
            is_error=True,
            response_message=str(e),
            ipaddress=ipaddress
        )

    except Exception as e:
        if con:
            con.rollback()

        logger.exception(
            "Unexpected error while creating price"
        )

        return _respond(
            body={
                "status": "error",
                "message": "Something went wrong",
                "error": str(e)
            },
            log_type=log_type,
            status=NOT_IMPLEMENTED,
            context=context,
            message_code=f"PC{NOT_IMPLEMENTED}",
            is_error=True,
            response_message=str(e),
            ipaddress=ipaddress
        )

    finally:
        if cursor:
            cursor.close()
        if con:
            con.close()
