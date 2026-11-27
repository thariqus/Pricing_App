import pymysql
from data.error_codes import INITIATING_FUNCTION, SERVICE_UNAVAILABLE, INTERNAL_SERVER_ERROR, NOT_IMPLEMENTED, SUCCESS, NOT_FOUND
from utils.log_response import _respond
from repository.mysql_connection import get_db_connection
from repository.query import permanently_remove_exp_logs_query
import os

PRICE_DB = os.getenv("DB_P_NAME")


def response_log(custom_message, code, error, response_message=None):
    return _respond(
        body={},
        custom_message=custom_message,
        ipaddress="",
        response_message=response_message,
        source="repository",
        log_type="Permanently remove expired log message",
        message_code=f"PP{code}",
        log_status=code,
        error=error
    )

def per_delete_log_message(filter_date):
    con = None
    cursor = None
    response_log("Enter into permanently remove expired log message function", INITIATING_FUNCTION, False)
    try:
        con = get_db_connection(PRICE_DB)
        cursor = con.cursor()

        # Get query and parameters
        query, params = permanently_remove_exp_logs_query(filter_date)
        # Execute query
        cursor.execute(query, params)
        # Check whether the site exists
        if cursor.rowcount == 0:
            con.rollback()
            response_log("No logs is deleted", NOT_FOUND, True)
            return ("", {"error" : True, "error_code" : NOT_FOUND})
        else:
            # Commit changes
            con.commit()
            response_log("permanently remove expired log completed", SUCCESS, False)
            return (cursor.rowcount, {"error" : False, "error_code" : SUCCESS})
    except ConnectionError as e:
        con.rollback()
        mysql_error_code = e.args[0] if e.args else None
        http_status = SERVICE_UNAVAILABLE if mysql_error_code in (2002, 2003, 2006, 2013) else INTERNAL_SERVER_ERROR

        response_log("Databse connection error, unable to connect database", http_status, True, str(e))

        return ("", {"error" : True, "error_code" : http_status})
    
    except pymysql.MySQLError as e:
        con.rollback()
        mysql_error_code = e.args[0] if e.args else None
        http_status = SERVICE_UNAVAILABLE if mysql_error_code in (2002, 2003, 2006, 2013) else INTERNAL_SERVER_ERROR

        response_log("Database error while permanently remove expired log message", http_status, True, str(e))
        
        return ("", {"error" : True, "error_code" : http_status})
    
    except Exception as e:
        con.rollback()
        response_log("Unexpected error while permanently remove expired log message", NOT_IMPLEMENTED, True, str(e))
        
        return ("", {"error" : True, "error_code" : NOT_IMPLEMENTED})
    finally:
        if cursor:
            cursor.close()

        if con:
            con.close()
