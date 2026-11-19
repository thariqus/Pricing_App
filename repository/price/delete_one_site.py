from flask import request
import pymysql
from repository.mysql_connection import get_db_connection
import os
from repository.query import delete_site_qry
from utils.log_response import _respond
from data.error_codes import INITIATING_FUNCTION, NOT_FOUND, SUCCESS, SERVICE_UNAVAILABLE, INTERNAL_SERVER_ERROR, NOT_IMPLEMENTED, BAD_REQUEST
from data.response import marshal_response_msg

PRICE_DB = os.getenv("DB_P_NAME")
SOURCE = "/api/delete_site/"

def response_log(custom_message, code, error, response_message=None):
    return _respond(
        body={},
        custom_message=custom_message,
        ipaddress=request.remote_addr,
        response_message=response_message,
        source="repository",
        log_type="Delete Site",
        message_code=f"PP{code}",
        log_status=code,
        error=error
    )


def delete_one_site(site_id):
    con = None
    cursor = None

    response_log("Entered in delete site function", INITIATING_FUNCTION, False)

    try:
        # Database connection
        con = get_db_connection(PRICE_DB)
        cursor = con.cursor()

        # Get query and parameters
        sel_query, params = delete_site_qry(site_id)

        # Execute query
        cursor.execute(sel_query, params)

        # Check whether a row was deleted
        if cursor.rowcount == 0:
            response_log("Error in deleting site", NOT_FOUND, True)
            return ("", {"error" : True, "error_code" : INTERNAL_SERVER_ERROR})

        response_log(f"Successfully deleted {cursor.rowcount} site", SUCCESS, False)

        # Commit changes
        con.commit()

        response_log("Successfully completed site deletion", SUCCESS, False)

        return (cursor.rowcount, {"error" : False, "error_code" : SUCCESS})
    
    except ConnectionError as e:
        mysql_error_code = e.args[0] if e.args else None
        http_status = SERVICE_UNAVAILABLE if mysql_error_code in (2002, 2003, 2006, 2013) else INTERNAL_SERVER_ERROR

        response_log("Databse connection error, unable to connect database", http_status, True, str(e))

        return ("", {"error" : True, "error_code" : http_status})
    
    except pymysql.MySQLError as e:
        mysql_error_code = e.args[0] if e.args else None
        http_status = SERVICE_UNAVAILABLE if mysql_error_code in (2002, 2003, 2006, 2013) else INTERNAL_SERVER_ERROR

        response_log("Database error while delete site data", http_status, True, str(e))
        
        return ("", {"error" : True, "error_code" : http_status})
    
    except Exception as e:
        response_log("Unexpected error while delete site data", NOT_IMPLEMENTED, True, str(e))
        
        return ("", {"error" : True, "error_code" : NOT_IMPLEMENTED})
    finally:
        if cursor:
            cursor.close()

        if con:
            con.close()
