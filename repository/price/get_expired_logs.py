from repository.mysql_connection import get_db_connection
import os
from utils.log_response import _respond
import pymysql
from data.error_codes import INITIATING_FUNCTION, SERVICE_UNAVAILABLE, INTERNAL_SERVER_ERROR, NOT_IMPLEMENTED, NOT_FOUND, SUCCESS
from repository.query import get_expired_log_message_query


PRICE_DB = os.getenv("DB_P_NAME")


def response_log(custom_message, code, error, response_message=None):
    return _respond(
        body={},
        custom_message=custom_message,
        ipaddress="",
        response_message=response_message,
        source="repository",
        log_type="Get all expired log datas",
        message_code=f"PP{code}",
        log_status=code,
        error=error
    )


def get_expired_logs(filter_date):
    con = None
    cursor = None
    response_log("Enter into get all expired log data function", INITIATING_FUNCTION, False)
    try:
        # Database connection
        con = get_db_connection(PRICE_DB)
        cursor = con.cursor()
        # Execute query
        sel_query, params = get_expired_log_message_query(filter_date)
        cursor.execute(sel_query, params)
        expired_log_data = cursor.fetchall()
        if not expired_log_data:
            response_log("No datas found", NOT_FOUND, True)
            return ("", {"error" : True, "error_code" : NOT_FOUND})
        
        response_log("Get all expired log message data completed", SUCCESS, False)
        return (expired_log_data, {"error" : False, "error_code" : SUCCESS})
    
    except ConnectionError as e:
        mysql_error_code = e.args[0] if e.args else None
        http_status = SERVICE_UNAVAILABLE if mysql_error_code in (2002, 2003, 2006, 2013) else INTERNAL_SERVER_ERROR

        response_log("Databse connection error, unable to connect database", http_status, True, str(e))

        return ("", {"error" : True, "error_code" : http_status})
    
    except pymysql.MySQLError as e:
        mysql_error_code = e.args[0] if e.args else None
        http_status = SERVICE_UNAVAILABLE if mysql_error_code in (2002, 2003, 2006, 2013) else INTERNAL_SERVER_ERROR

        response_log("Database error while select all expired log message datas", http_status, True, str(e))
        
        return ("", {"error" : True, "error_code" : http_status})
    
    except Exception as e:
        response_log("Unexpected error while select all expired log message datas", NOT_IMPLEMENTED, True, str(e))
        
        return ("", {"error" : True, "error_code" : NOT_IMPLEMENTED})
    finally:
        if cursor:
            cursor.close()
        if con:
            con.close()