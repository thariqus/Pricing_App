from flask import jsonify, request
import pymysql
from repository.mysql_connection import get_db_connection
import os
from repository.query import select_one_sites
from utils.log_response import _respond
from data.error_codes import INITIATING_FUNCTION, SUCCESS, SERVICE_UNAVAILABLE, INTERNAL_SERVER_ERROR, NOT_FOUND, NOT_IMPLEMENTED

PRICE_DB = os.getenv("DB_P_NAME")
SOURCE = ""

def response_log(custom_message, code, error, response_message=None):
    return _respond(
        body={},
        custom_message=custom_message,
        ipaddress=request.remote_addr,
        response_message=response_message,
        source="repository",
        log_type="Get one site datas",
        message_code=f"PP{code}",
        log_status=code,
        error=error
    )

def get_one_site_data(site):
    con = None
    cursor = None
    response_log("Enter into get one site data function", INITIATING_FUNCTION, False)
    try:
        # Database connection
        con = get_db_connection(PRICE_DB)
        cursor = con.cursor()
        # Execute query
        sel_query, params = select_one_sites(site)
        cursor.execute(sel_query, params)
        one_site_datas = cursor.fetchall()
        if not one_site_datas:
            response_log("No datas found", NOT_FOUND, True)
            return ("", {"error" : True, "error_code" : NOT_FOUND})
        
        response_log("Get one site data completed", SUCCESS, False)
        return (one_site_datas, {"error" : False, "error_code" : SUCCESS})
    
    except ConnectionError as e:
        mysql_error_code = e.args[0] if e.args else None
        http_status = SERVICE_UNAVAILABLE if mysql_error_code in (2002, 2003, 2006, 2013) else INTERNAL_SERVER_ERROR

        response_log("Databse connection error, unable to connect database", http_status, True, str(e))

        return ("", {"error" : True, "error_code" : http_status})
    
    except pymysql.MySQLError as e:
        mysql_error_code = e.args[0] if e.args else None
        http_status = SERVICE_UNAVAILABLE if mysql_error_code in (2002, 2003, 2006, 2013) else INTERNAL_SERVER_ERROR

        response_log("Database error while select one site datas", http_status, True, str(e))
        
        return ("", {"error" : True, "error_code" : http_status})
    
    except Exception as e:
        response_log("Unexpected error while select one site datas", NOT_IMPLEMENTED, True, str(e))
        
        return ("", {"error" : True, "error_code" : NOT_IMPLEMENTED})
    finally:
        if cursor:
            cursor.close()
        if con:
            con.close()