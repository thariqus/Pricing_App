from flask import request
from repository.mysql_connection import get_db_connection
from repository.query import get_data_replication
import pymysql
import os
from utils.log_response import _respond
from data.error_codes import INITIATING_FUNCTION, SUCCESS, SERVICE_UNAVAILABLE, INTERNAL_SERVER_ERROR, NOT_FOUND, NOT_IMPLEMENTED
from data.response import marshal_response_msg

PRICE_DB = os.getenv("DB_P_NAME")
SOURCE = "/api/items/get_repliaction_data/"

def response_log(custom_message, code, error, response_message=None):
    return _respond(
        body={},
        custom_message=custom_message,
        ipaddress=request.remote_addr,
        response_message=response_message,
        source="repository",
        log_type="Get replication store data",
        message_code=f"PP{code}",
        log_status=code,
        error=error
    )

def get_replication_store_data(version_id, site_id):
    con = None
    cursor = None
    response_log("Enter into get replication store data function", INITIATING_FUNCTION, False)
    try:            
        # Database connection
        con = get_db_connection(PRICE_DB)
        cursor = con.cursor()
        # Execute query
        sel_query, params = get_data_replication(version_id, site_id) #get the site code automatically
        cursor.execute(sel_query, params)
        replication_data = cursor.fetchall()
        if not replication_data:
            response_log("No data found", NOT_FOUND, True)
            return ("", {"error" : True, "error_code" : NOT_FOUND})
            
        response_log("Enter into get replication store data completed", SUCCESS, False)
        return (replication_data, {"error" : False, "error_code" : SUCCESS})
        
    except ConnectionError as e:
        mysql_error_code = e.args[0] if e.args else None
        http_status = SERVICE_UNAVAILABLE if mysql_error_code in (2002, 2003, 2006, 2013) else INTERNAL_SERVER_ERROR

        response_log("Databse connection error, unable to connect database", http_status, True, str(e))

        return ("", {
            "error" : True, 
            "error_code" : http_status})
    
    except pymysql.MySQLError as e:
        mysql_error_code = e.args[0] if e.args else None
        http_status = SERVICE_UNAVAILABLE if mysql_error_code in (2002, 2003, 2006, 2013) else INTERNAL_SERVER_ERROR

        response_log("Database error while fetch replication data", http_status, True, str(e))
        
        return ("", {
            "error" : True, 
            "error_code" : http_status})
    
    except Exception as e:
        response_log("Unexpected error while fetch replication data", NOT_IMPLEMENTED, True, str(e))
        
        return ("", {
            "error" : True, 
            "error_code" : NOT_IMPLEMENTED})
    finally:
        if cursor:
            cursor.close()
        if con:
            con.close()