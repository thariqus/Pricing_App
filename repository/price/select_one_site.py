from flask import request
from repository.mysql_connection import get_db_connection
import os
import pymysql
from repository.query import select_one_sites
from utils.log_response import _respond
from data.error_codes import INITIATING_FUNCTION, SUCCESS, SERVICE_UNAVAILABLE, INTERNAL_SERVER_ERROR, NOT_IMPLEMENTED, NOT_FOUND

PRICE_DB = os.getenv("DB_P_NAME")

def response_log(custom_message, code, error, response_message=None):
    return _respond(
        body={},
        custom_message=custom_message,
        ipaddress=request.remote_addr,
        response_message=response_message,
        source="repository",
        log_type="Select one site details",
        message_code=f"PP{code}",
        log_status=code,
        error=error
    )


def select_one_site(site_code):
    con = None
    cursor = None
    response_log("Entered in select one site details function", INITIATING_FUNCTION, False)
    try:
        # Database connection
        con = get_db_connection(PRICE_DB)
        cursor = con.cursor()
        # Execute query
        
        select_sql, select_params = select_one_sites(site_code)
        cursor.execute(select_sql, select_params)
        site_datas = cursor.fetchall()

        if len(site_datas) <= 0:
            return ("", {"error" : True, "error_code" : NOT_FOUND})
        
        response_log(f"{len(site_datas)} Sites created successfully", SUCCESS, False)

        response_log("Site setting completed successfully", SUCCESS, False)

        return (site_datas, {"error" : False, "error_code" : SUCCESS})

    except ConnectionError as e:
        mysql_error_code = e.args[0] if e.args else None
        http_status = SERVICE_UNAVAILABLE if mysql_error_code in (2002, 2003, 2006, 2013) else INTERNAL_SERVER_ERROR

        response_log("Databse connection error, unable to connect database", http_status, True, str(e))

        return ("", {"error" : True, "error_code" : http_status})
    
    except pymysql.MySQLError as e:
        mysql_error_code = e.args[0] if e.args else None
        http_status = SERVICE_UNAVAILABLE if mysql_error_code in (2002, 2003, 2006, 2013) else INTERNAL_SERVER_ERROR

        response_log("Database error while select one site data", http_status, True, str(e))
        
        return ("", {"error" : True, "error_code" : http_status})
    
    except Exception as e:
        response_log("Unexpected error while select one site data", NOT_IMPLEMENTED, True, str(e))
        
        return ("", {"error" : True, "error_code" : NOT_IMPLEMENTED})

    finally:
        if cursor:
            cursor.close()
        if con:
            con.close()