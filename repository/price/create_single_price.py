from flask import request, jsonify
import pymysql
from repository.mysql_connection import get_db_connection
from utils.log_error import logger
from repository.query import insert_price_query, create_logger, get_latest_version_id_query, insert_version_query  
from repository.price.create_log import write_log
from data.error_codes import (
    INITIAL_FUNCTION
)
import os

LOG_SOURCE = "single_item"
LOG_TYPE = "PRICE_INSERT"

PRICE_DB = os.getenv("DB_P_NAME")

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


def create_single_price(data):
    # _respond(
    #     {"message" : "Success"},
    #     INITIAL_FUNCTION, 
    #     "Entered in single item price function",
    #     INITIAL_FUNCTION,
    #     False,
    #     response_message="Entered in single item price function"
    # )
    con = None
    cursor = None
    context = "Single Item Price"
    try:
        if not data:
            return _respond(
                {"status": "error", "message": "Request data is empty or invalid"},
                400, context, "PP400", True
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
        logger_sql_query, logger_params = create_logger(request.remote_addr,"Insert Single Item Price Data")
        cursor.execute(logger_sql_query, logger_params)
        con.commit()

        if inserted_id:
            version_sql, version_params = insert_version_query({
                "id": version_id,
                "file_name": "",
                "record_count": 1,
            })
            cursor.execute(version_sql, version_params)
            con.commit()

        return _respond(
            {"data": inserted_id },
            200, context, "PP200", False,
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
            503, context, "PC503", True, response_message=str(e)
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
            500, context, "PC500", True, response_message=str(e)
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
            500, context, "PC501", True, response_message=str(e)
        )

    finally:
        if cursor:
            cursor.close()
        if con:
            con.close()