from flask import request
from repository.mysql_connection import get_db_connection
import os
from repository.query import select_all_prices
import pymysql
from utils.log_response import _respond
from data.response import marshal_response_msg
from data.error_codes import INITIATING_FUNCTION, BAD_REQUEST, SUCCESS, SERVICE_UNAVAILABLE, INTERNAL_SERVER_ERROR, NOT_FOUND, NOT_IMPLEMENTED

PRICE_DB = os.getenv("DB_P_NAME")
SOURCE = "/api/items/fetch_all_item_prices"

def response_log(custom_message, code, error, response_message=None):
    return _respond(
        body={},
        custom_message=custom_message,
        ipaddress=request.remote_addr,
        response_message=response_message,
        source="repository",
        log_type="Fetch all prices",
        message_code=f"PP{code}",
        log_status=code,
        error=error
    )


def fetch_all_prices():
    con = None
    cursor = None
    response_log("Enter into fetch all price", INITIATING_FUNCTION, False)
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
                "limit" : limit,
                "total_records" : ""
                })
        
        if limit < 1 or limit > 100:
            response_log("Limit must be between 1 and 100", BAD_REQUEST, True)
            return ("", {
                "error" : True, 
                "error_code" : BAD_REQUEST,
                "page" : page,
                "limit" : limit,
                "total_records" : ""
                })

            
        # Database connection
        con = get_db_connection(PRICE_DB)
        cursor = con.cursor()
        # Execute query
        sel_query, count_query, params = select_all_prices(page, limit)
        cursor.execute(sel_query, params)
        price_data = cursor.fetchall()
        cursor.execute(count_query)
        total_records = cursor.fetchone()["total"]
        

        response_log("Price selected successfully", SUCCESS, False)
        return ({"data" : price_data,
                "page" : page,
                "limit" : limit,
                "total_records" : total_records
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
            "limit" : limit,
            "total_records" : ""})
    
    except pymysql.MySQLError as e:
        mysql_error_code = e.args[0] if e.args else None
        http_status = SERVICE_UNAVAILABLE if mysql_error_code in (2002, 2003, 2006, 2013) else INTERNAL_SERVER_ERROR

        response_log("Database error while fech all prices", http_status, True, str(e))
        
        return ("", {
            "error" : True, 
            "error_code" : http_status,
            "page" : page,
            "limit" : limit,
            "total_records" : ""})
    
    except Exception as e:
        response_log("Unexpected error while fetch all price", NOT_IMPLEMENTED, True, str(e))
        
        return ("", {
            "error" : True, 
            "error_code" : NOT_IMPLEMENTED,
            "page" : page,
            "limit" : limit,
            "total_records" : ""})
    finally:
        if cursor:
            cursor.close()
        if con:
            con.close()