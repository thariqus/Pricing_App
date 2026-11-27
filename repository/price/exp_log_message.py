import pymysql
from data.error_codes import INITIATING_FUNCTION, SERVICE_UNAVAILABLE, INTERNAL_SERVER_ERROR, NOT_IMPLEMENTED, SUCCESS
from utils.log_response import _respond
from repository.mysql_connection import get_db_connection
from repository.query import insert_expired_log_message_query
import os

PRICE_DB = os.getenv("DB_P_NAME")


def response_log(custom_message, code, error, response_message=None):
    return _respond(
        body={},
        custom_message=custom_message,
        ipaddress="",
        response_message=response_message,
        source="repository",
        log_type="Moved expired log message",
        message_code=f"PP{code}",
        log_status=code,
        error=error
    )

def exp_log_message(data):
    con = None
    cursor = None
    response_log("Enter into create expired log message function", INITIATING_FUNCTION, False)
    try:
        con = get_db_connection(PRICE_DB)
        cursor = con.cursor()

        # Get query and parameters
        expired_logs = [
            (
                log['custom_message'],
                log['response_message'],
                log['source'],
                log['type'],
                log['ipaddress'],
                log['site_details'],
                log['message_code'],
                log['log_status'],
                log['info'],
                log['error']
            )
            for log in data
        ]
        query, params = insert_expired_log_message_query(expired_logs)

        # Execute query
        cursor.executemany(query, params)

        # Check whether the site exists
        if cursor.rowcount != len(expired_logs):
            con.rollback()
            response_log("Something went wrong, can't move the log message", INTERNAL_SERVER_ERROR, True)
            return ("", {"error" : True, "error_code" : INTERNAL_SERVER_ERROR})
        else:
            response_log(f"Successfully moved {cursor.rowcount} log message", SUCCESS, False)
            # Commit changes
            con.commit()

            response_log("Create expired log completed", SUCCESS, False)
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

        response_log("Database error while insert expired log message", http_status, True, str(e))
        
        return ("", {"error" : True, "error_code" : http_status})
    
    except Exception as e:
        con.rollback()
        response_log("Unexpected error while insert expired log message", NOT_IMPLEMENTED, True, str(e))
        
        return ("", {"error" : True, "error_code" : NOT_IMPLEMENTED})
    finally:
        if cursor:
            cursor.close()

        if con:
            con.close()
