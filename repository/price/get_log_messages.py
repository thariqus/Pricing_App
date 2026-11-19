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
            return ("", {
                "error" : True, 
                "error_code" : BAD_REQUEST,
                "page" : page,
                "limit" : limit
            })
        if limit < 1 or limit > 100:
            response_log("Limit must be between 1 and 100", BAD_REQUEST, True)
            return ("", {
                "error" : True, 
                "error_code" : BAD_REQUEST,
                "page" : page,
                "limit" : limit
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
            return ("", {
                "error" : True, 
                "error_code" : NOT_FOUND, 
                "page" : page,
                "limit" : limit
            })
        response_log("Get log message completed", SUCCESS, False)
        return ({"data" : log_messages,
            "page" : page,
            "limit" : limit
            }
            , {"error" : False, "error_code" : SUCCESS})
        
    except ConnectionError as e:
        mysql_error_code = e.args[0] if e.args else None
        http_status = SERVICE_UNAVAILABLE if mysql_error_code in (2002, 2003, 2006, 2013) else INTERNAL_SERVER_ERROR

        response_log("Databse connection error, unable to connect database", http_status, True, str(e))

        return ("", {
            "error" : True, 
            "error_code" : http_status,
            "page" : page,
            "limit" : limit})
    
    except pymysql.MySQLError as e:
        mysql_error_code = e.args[0] if e.args else None
        http_status = SERVICE_UNAVAILABLE if mysql_error_code in (2002, 2003, 2006, 2013) else INTERNAL_SERVER_ERROR

        response_log("Database error while fetch all log message", http_status, True, str(e))
        
        return ("", {
            "error" : True, 
            "error_code" : http_status,
            "page" : page,
            "limit" : limit})
    
    except Exception as e:
        response_log("Unexpected error while fetch all log message", NOT_IMPLEMENTED, True, str(e))
        
        return ("", {
            "error" : True, 
            "error_code" : NOT_IMPLEMENTED,
            "page" : page,
            "limit" : limit})
    finally:
        if cursor:
            cursor.close()
        if con:
            con.close()