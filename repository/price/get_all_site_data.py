from flask import jsonify, request
import pymysql
from repository.mysql_connection import get_db_connection
import os
from repository.query import select_all_sites
from utils.log_response import _respond
from data.error_codes import INITIATING_FUNCTION, SUCCESS, SERVICE_UNAVAILABLE, INTERNAL_SERVER_ERROR, NOT_FOUND, NOT_IMPLEMENTED
from data.response import marshal_response_msg

PRICE_DB = os.getenv("DB_P_NAME")
SOURCE = "/api/get_all_sites"

def response_log(custom_message, code, error, response_message=None):
    return _respond(
        body={},
        custom_message=custom_message,
        ipaddress=request.remote_addr,
        response_message=response_message,
        source="repository",
        log_type="Get all site datas",
        message_code=f"PP{code}",
        log_status=code,
        error=error
    )

def get_all_site_data():
    con = None
    cursor = None
    response_log("Enter into get all site data function", INITIATING_FUNCTION, False)
    try:
        # Database connection
        con = get_db_connection(PRICE_DB)
        cursor = con.cursor()
        # Execute query
        sel_query = select_all_sites()
        cursor.execute(sel_query)
        site_datas = cursor.fetchall()
        if not site_datas:
            response_log("No datas found", NOT_FOUND, True)
            return marshal_response_msg({
                "error_message" : "No data found",
                "erroe_details" : "There is no site datas",
                "error_code" : NOT_FOUND,
                "is_error" : True
            })
        response_log("Get all site data completed", SUCCESS, False)
        return marshal_response_msg({
            "data" : site_datas,
            "success_message" : "Site selected successfully",
            "success_code" : SUCCESS,
            "source" : SOURCE,
            "is_error" : False
        })
    except ConnectionError as e:
        response_log("Databse connection error, unable to connect database", SERVICE_UNAVAILABLE, True, str(e))
        return marshal_response_msg({
            "error_message" : "Databse connection error, unable to connect database",
            "error_details" : str(e),
            "error_code" : SERVICE_UNAVAILABLE,
            "is_error" : True
        })
    except pymysql.MySQLError as e:
        response_log("Database error while fetching all site data", INTERNAL_SERVER_ERROR, True, str(e))
        return marshal_response_msg({
            "error_message" : "Database error while fetching all site data",
            "error_details" : str(e),
            "error_code" : INTERNAL_SERVER_ERROR,
            "is_error" : True
        })
    except Exception as e:
        response_log("Unexpected error while fetching all site data", NOT_IMPLEMENTED, True, str(e))
        return marshal_response_msg({
            "error_message" : "Unexpected error while fetching all site data",
            "error_details" : str(e),
            "error_code" : NOT_IMPLEMENTED,
            "is_error" : True
        })
    finally:
        if cursor:
            cursor.close()
        if con:
            con.close()