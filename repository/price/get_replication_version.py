from flask import request
from repository.mysql_connection import get_db_connection
from repository.query import get_replicated_version
import pymysql
import os
from utils.log_response import _respond
from data.error_codes import INITIATING_FUNCTION, SUCCESS, SERVICE_UNAVAILABLE, INTERNAL_SERVER_ERROR, BAD_REQUEST, NOT_IMPLEMENTED
from data.response import marshal_response_msg

PRICE_DB = os.getenv("DB_P_NAME")
SOURCE = "/api/items/site_details/"

def response_log(custom_message, code, error, response_message=None):
    return _respond(
        body={},
        custom_message=custom_message,
        ipaddress=request.remote_addr,
        response_message=response_message,
        source="repository",
        log_type="Get replication version data",
        message_code=f"PP{code}",
        log_status=code,
        error=error
    )

def get_replication_version_data(site_code):
    con = None
    cursor = None
    response_log("Enter into get replication version data function", INITIATING_FUNCTION, False)
    try:
        if not site_code:
            response_log("site code not found", BAD_REQUEST, True)
            return marshal_response_msg({
                "error_message" : "Site code not found",
                "error_details" : "Site code is required, please provide a valid site code",
                "error_code" : BAD_REQUEST,
                "is_error" : True
            })
        # Database connection
        con = get_db_connection(PRICE_DB)
        cursor = con.cursor()
        # Execute query

        rep_qry, rep_params = get_replicated_version(site_code)
        cursor.execute(rep_qry, rep_params)

        row = cursor.fetchone()
        version = row[0] if row else 0

        response_log("Enter into get replication version data completed", SUCCESS, False)

        return marshal_response_msg({
            "custom_field" : {
                "version" : int(version)
            },
            "success_message" : "Successfully selected version",
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
        response_log("Database error while fetching replication version data", INTERNAL_SERVER_ERROR, True, str(e))
        return marshal_response_msg({
            "error_message" : "Database error while fetching replication version data",
            "error_details" : str(e),
            "error_code" : INTERNAL_SERVER_ERROR,
            "is_error" : True
        })
    except Exception as e:
        response_log("Unexpected error while fetching replication version data", NOT_IMPLEMENTED, True, str(e))
        return marshal_response_msg({
            "error_message" : "Unexpected error while fetching replication version data",
            "error_details" : str(e),
            "error_code" : NOT_IMPLEMENTED,
            "is_error" : True
        })
    finally:
        if cursor:
            cursor.close()
        if con:
            con.close()