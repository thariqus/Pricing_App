from flask import request
import os
from repository.query import get_prices_from_version_query
from repository.mysql_connection import get_db_connection
from utils.log_response import _respond
import pymysql
from data.error_codes import SERVICE_UNAVAILABLE, INTERNAL_SERVER_ERROR, INITIATING_FUNCTION, SUCCESS, NOT_FOUND, NOT_IMPLEMENTED

SOURCE = "/api/items/prices/version/"

def response_log(custom_message, code, error, response_message=None):
    return _respond(
        body={},
        custom_message=custom_message,
        ipaddress=request.remote_addr,
        response_message=response_message,
        source="repository",
        log_type="Fetch HO price by version",
        message_code=f"PP{code}",
        log_status=code,
        error=error
    )


def get_prices_from_version(version_id, site_code, skip=0):
    con = None
    response_log("Enter into fetch ho price by version", INITIATING_FUNCTION, False)
    try:
        con = get_db_connection(os.getenv("DB_P_NAME"))
        with con.cursor() as cursor:
            sql_query, params = get_prices_from_version_query(version_id, site_code, skip)
            cursor.execute(sql_query, params)
            data = cursor.fetchall()
            if not data:
                response_log("No data found", NOT_FOUND, True)
                return ("", {"error" : True, "error_code" : NOT_FOUND})
            response_log("Completed HO price fetch completed", SUCCESS, False)
            return ({
                "data" : data,
                "version_id" : version_id,
                "count" : len(data)
            },
            {"error" : False, "error_code" : SUCCESS})
        
    except ConnectionError as e:
        mysql_error_code = e.args[0] if e.args else None
        http_status = SERVICE_UNAVAILABLE if mysql_error_code in (2002, 2003, 2006, 2013) else INTERNAL_SERVER_ERROR

        response_log("Databse connection error, unable to connect database", http_status, True, str(e))

        return ("", {"error" : True, "error_code" : http_status})
    
    except pymysql.MySQLError as e:
        mysql_error_code = e.args[0] if e.args else None
        http_status = SERVICE_UNAVAILABLE if mysql_error_code in (2002, 2003, 2006, 2013) else INTERNAL_SERVER_ERROR

        response_log("Database error while get price version data", http_status, True, str(e))
        
        return ("", {"error" : True, "error_code" : http_status})
    
    except Exception as e:
        response_log("Unexpected error while get price version data", NOT_IMPLEMENTED, True, str(e))
        
        return ("", {"error" : True, "error_code" : NOT_IMPLEMENTED})
    finally:
        if con:
            con.close()