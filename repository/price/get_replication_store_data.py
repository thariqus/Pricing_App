from flask import request
from repository.mysql_connection import get_db_connection
from repository.query import get_data_replication
import pymysql
import os
from utils.log_response import _respond
from data.error_codes import INITIATING_FUNCTION, SUCCESS, SERVICE_UNAVAILABLE, INTERNAL_SERVER_ERROR, NOT_FOUND, BAD_REQUEST, NOT_IMPLEMENTED
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
        if version_id is None or version_id == "":
            response_log("Version id not found", BAD_REQUEST, True)
            return marshal_response_msg({
                "error_message" : "Version Id not found",
                "error_details" : "Version Id is required, please give a valid version Id",
                "error_code" : BAD_REQUEST,
                "is_error" : True
            })

        if site_id is None or site_id == "":
            response_log("Site code not found", BAD_REQUEST, True)
            return marshal_response_msg({
                "error_message" : "Site code not found",
                "error_details" : "Site code is required, please give a valid site code",
                "error_code" : BAD_REQUEST,
                "is_error" : True
            })
            
        # Database connection
        con = get_db_connection(PRICE_DB)
        cursor = con.cursor()
        # Execute query
        sel_query, params = get_data_replication(version_id, site_id) #get the site code automatically
        cursor.execute(sel_query, params)
        replication_data = cursor.fetchall()
        if not replication_data:
            response_log("No data found", NOT_FOUND, True)
            return marshal_response_msg({
                "error_message" : "No data found",
                "error_details" : f"No data found based {version_id} version in {site_id} store",
                "error_code" : NOT_FOUND,
                "is_error" : True
            })
        response_log("Enter into get replication store data completed", SUCCESS, False)
        return marshal_response_msg({
            "data" : replication_data,
            "success_message" : "Successfully selected replication data",
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
        response_log("Database error while fetching replication store data", INTERNAL_SERVER_ERROR, True, str(e))
        return marshal_response_msg({
            "error_message" : "Database error while fetching replication store data",
            "error_details" : str(e),
            "error_code" : INTERNAL_SERVER_ERROR,
            "is_error" : True
        })
    except Exception as e:
        response_log("Unexpected error while fetching replication store data", NOT_IMPLEMENTED, True, str(e))
        return marshal_response_msg({
            "error_message" : "Unexpected error while fetching replication store data",
            "error_details" : str(e),
            "error_code" : NOT_IMPLEMENTED,
            "is_error" : True
        })
    finally:
        if cursor:
            cursor.close()
        if con:
            con.close()