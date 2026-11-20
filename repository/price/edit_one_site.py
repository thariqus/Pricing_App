from flask import request
import pymysql
from repository.mysql_connection import get_db_connection
import os
from repository.query import update_site_qry
from utils.log_response import _respond
from data.error_codes import INITIATING_FUNCTION, NOT_FOUND, SUCCESS, SERVICE_UNAVAILABLE, INTERNAL_SERVER_ERROR, BAD_REQUEST, NOT_IMPLEMENTED
from data.response import marshal_response_msg

PRICE_DB = os.getenv("DB_P_NAME")
SOURCE = "/api/update_site/"

def response_log(custom_message, code, error, response_message=None):
    return _respond(
        body={},
        custom_message=custom_message,
        ipaddress=request.remote_addr,
        response_message=response_message,
        source="repository",
        log_type="Edit Site",
        message_code=f"PP{code}",
        log_status=code,
        error=error
    )


def edit_one_site(site_id, data):
    con = None
    cursor = None

    response_log("Entered in edit site function", INITIATING_FUNCTION, False)
    try:
        # Database connection
        con = get_db_connection(PRICE_DB)
        cursor = con.cursor()

        # Get query and parameters
        update_query, params = update_site_qry(site_id, data)

        # Execute query
        cursor.execute(update_query, params)

        # Check whether the site exists
        if cursor.rowcount == 0:
            con.rollback()
            response_log("No changes made", NOT_FOUND, True)
            return ("", {"error" : True, "error_code" : BAD_REQUEST})

        response_log(f"Successfully edited {cursor.rowcount} site", SUCCESS, False)

        # Commit changes
        con.commit()

        response_log("Edit site completed", SUCCESS, False)
        return (cursor.rowcount, {"error" : False, "error_code" : SUCCESS})

    except ConnectionError as e:
        mysql_error_code = e.args[0] if e.args else None
        http_status = SERVICE_UNAVAILABLE if mysql_error_code in (2002, 2003, 2006, 2013) else INTERNAL_SERVER_ERROR

        response_log("Databse connection error, unable to connect database", http_status, True, str(e))

        return ("", {"error" : True, "error_code" : http_status})
    
    except pymysql.MySQLError as e:
        mysql_error_code = e.args[0] if e.args else None
        http_status = SERVICE_UNAVAILABLE if mysql_error_code in (2002, 2003, 2006, 2013) else INTERNAL_SERVER_ERROR

        response_log("Database error while edit site data", http_status, True, str(e))
        
        return ("", {"error" : True, "error_code" : http_status})
    
    except Exception as e:
        response_log("Unexpected error while edit site data", NOT_IMPLEMENTED, True, str(e))
        
        return ("", {"error" : True, "error_code" : NOT_IMPLEMENTED})
    finally:
        if cursor:
            cursor.close()

        if con:
            con.close()
