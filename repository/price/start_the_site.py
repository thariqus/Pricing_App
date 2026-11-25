from flask import request
import os
from utils.log_response import _respond
from repository.mysql_connection import get_db_connection
from data.error_codes import INITIATING_FUNCTION, INTERNAL_SERVER_ERROR, SUCCESS, NOT_IMPLEMENTED, SERVICE_UNAVAILABLE
from repository.query import site_permission
import pymysql

PRICE_DB = os.getenv("DB_P_NAME")


def response_log(custom_message, code, error, response_message=None):
    return _respond(
        body={},
        custom_message=custom_message,
        ipaddress=request.remote_addr,
        response_message=response_message,
        source="repository",
        log_type="Site start",
        message_code=f"PP{code}",
        log_status=code,
        error=error
    )

def start_the_site(location_code):
    con = None
    cursor = None

    response_log("Entered in site start function", INITIATING_FUNCTION, False)

    try:
        # Database connection
        con = get_db_connection(PRICE_DB)
        cursor = con.cursor()

        # Get query and parameters
        sel_query, params = site_permission(location_code, 1)

        # Execute query
        cursor.execute(sel_query, params)

        # Check whether a row was deleted
        if cursor.rowcount == 0:
            response_log("Error in site starting", INTERNAL_SERVER_ERROR, True)
            return ("", {"error" : True, "error_code" : INTERNAL_SERVER_ERROR})

        response_log(f"Successfully started {cursor.rowcount} site", SUCCESS, False)

        # Commit changes
        con.commit()

        response_log("Successfully completed site starting function", SUCCESS, False)

        return (cursor.rowcount, {"error" : False, "error_code" : SUCCESS})
    
    except ConnectionError as e:
        mysql_error_code = e.args[0] if e.args else None
        http_status = SERVICE_UNAVAILABLE if mysql_error_code in (2002, 2003, 2006, 2013) else INTERNAL_SERVER_ERROR

        response_log("Databse connection error, unable to connect database", http_status, True, str(e))

        return ("", {"error" : True, "error_code" : http_status})
    
    except pymysql.MySQLError as e:
        mysql_error_code = e.args[0] if e.args else None
        http_status = SERVICE_UNAVAILABLE if mysql_error_code in (2002, 2003, 2006, 2013) else INTERNAL_SERVER_ERROR

        response_log("Database error while start site", http_status, True, str(e))
        
        return ("", {"error" : True, "error_code" : http_status})
    
    except Exception as e:
        response_log("Unexpected error while start site", NOT_IMPLEMENTED, True, str(e))
        
        return ("", {"error" : True, "error_code" : NOT_IMPLEMENTED})
    finally:
        if cursor:
            cursor.close()

        if con:
            con.close()
    