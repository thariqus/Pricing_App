from flask import request
from repository.mysql_connection import get_db_connection
from repository.query import select_log_message
import os
import pymysql
from utils.log_response import _respond
from data.error_codes import INITIATING_FUNCTION, BAD_REQUEST, SUCCESS, SERVICE_UNAVAILABLE, INTERNAL_SERVER_ERROR, NOT_FOUND, NOT_IMPLEMENTED
from data.response import marshal_response_msg

PRICE_DB = os.getenv("DB_P_NAME")

def response_log(custom_message, code, error, response_message=None):
    return _respond(
        body={},
        custom_message=custom_message,
        ipaddress=request.remote_addr,
        response_message=response_message,
        source="repository",
        log_type="Get log message",
        message_code=f"PP{code}",
        log_status=code,
        error=error
    )

def get_log_messages():
    con = None
    cursor = None
    response_log("Enter into get log message function", INITIATING_FUNCTION, False)
    try:
        # Get pagination values
        page = request.args.get("page", default=1, type=int)
        limit = request.args.get("limit", default=100, type=int)
        # Validate pagination
        if page < 1:
            response_log("Page must be greater than 0", BAD_REQUEST, True)
            return marshal_response_msg({
                "error_message" : "Page must be greater that 0",
                "error_details" : "Provided page is below 0,please provide a valid page number",
                "error_code" : BAD_REQUEST,
                "is_error" : True
            })
        if limit < 1 or limit > 100:
            response_log("Limit must be between 1 and 100", BAD_REQUEST, True)
            return marshal_response_msg({
                "error_message" : "Limit must be between 1 and 100",
                "error_details" : "Provided limit is below 1 or above 100,please provide a valid limit between 1 and 100",
                "error_code" : BAD_REQUEST,
                "is_error" : True
            })
        # Database connection
        con = get_db_connection(PRICE_DB)
        cursor = con.cursor()
        # Execute query
        sel_query, params = select_log_message(page, limit)
        cursor.execute(sel_query, params)
        log_messages = cursor.fetchall()
        if not log_messages:
            response_log("No data found", NOT_FOUND, True)
            return marshal_response_msg({
                "error_message" : "No data found",
                "error_details" : "There is no log message found",
                "error_code" : NOT_FOUND,
                "is_error" : True
            })
        response_log("Get log message completed", SUCCESS, False)
        return marshal_response_msg({
            "data" : log_messages,
            "success_message" : "Successfully selected log message",
            "success_code" : SUCCESS,
            "is_error" : False
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
        response_log("Database error while fetching all log message", INTERNAL_SERVER_ERROR, True, str(e))
        return marshal_response_msg({
            "error_message" : "Database error while fetching all log message",
            "error_details" : str(e),
            "error_code" : INTERNAL_SERVER_ERROR,
            "is_error" : True
        })
    except Exception as e:
        response_log("Unexpected error while fetching all log message data", NOT_IMPLEMENTED, True, str(e))
        return marshal_response_msg({
            "error_message" : "Unexpected error while fetching all log message data",
            "error_details" : str(e),
            "error_code" : NOT_IMPLEMENTED,
            "is_error" : True
        })
    finally:
        if cursor:
            cursor.close()
        if con:
            con.close()