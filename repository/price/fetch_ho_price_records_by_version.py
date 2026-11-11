from flask import request
import os
from repository.query import get_prices_from_version_query
from repository.mysql_connection import get_db_connection
from utils.log_response import _respond
import pymysql
from data.error_codes import SERVICE_UNAVAILABLE, INTERNAL_SERVER_ERROR, INITIATING_FUNCTION, SUCCESS, NOT_FOUND, NOT_IMPLEMENTED, BAD_REQUEST
from data.response import marshal_response_msg

SOURCE = "/api/items/prices/version/"

def response_log(custom_message, code, error, response_message=None):
    return _respond(
        body={},
        custom_message=custom_message,
        ipaddress=request.remote_addr,
        response_message=response_message,
        source="repository",
        log_type="Fetch HO price by version",
        message_code=f"PP{code}",
        log_status=code,
        error=error
    )


def get_prices_from_version(version_id, site_code, skip=0):
    con = None
    response_log("Enter into fetch ho price by version", INITIATING_FUNCTION, False)
    try:
        con = get_db_connection(os.getenv("DB_P_NAME"))
        if version_id is None or version_id == "":
            response_log("Version Id not found", BAD_REQUEST, True)
            return marshal_response_msg({
                "error_message" : "Version Id not found",
                "error_details" : "Version id is required, but not given, please provide a valid version id",
                "error_code" : BAD_REQUEST,
                "is_error" : True
            })


        if site_code is None or site_code == "":
            response_log("Site code not found", BAD_REQUEST, True)
            return marshal_response_msg({
                "error_message" : "Site code not found",
                "error_details" : "Site code is required, but not given, please provide a valid site code",
                "error_code" : BAD_REQUEST,
                "is_error" : True
            })

        with con.cursor() as cursor:
            sql_query, params = get_prices_from_version_query(version_id, site_code, skip)
            cursor.execute(sql_query, params)
            data = cursor.fetchall()
            if not data:
                response_log("No data found", NOT_FOUND, True)
                return marshal_response_msg({
                    "error_message" : "No data found",
                    "error_details" : "There is no data in the condition",
                    "error_code" : NOT_FOUND,
                    "is_error" : True
                })
            response_log("Completed HO price fetch completed", SUCCESS, False)
            return marshal_response_msg({
                "data" : data,
                "success_message" : "Successfully selected price by version",
                "success_code" : SUCCESS,
                "source" : SOURCE,
                "is_error" : False,
                "custom_field" : {
                    "version_id" : version_id,
                    "count" : len(data)
                }
            })
    except ConnectionError as e:
        response_log("Unable to connect to database", SERVICE_UNAVAILABLE, True, str(e))
        return marshal_response_msg({
            "error_message" : "Unable to connect to database",
            "error_details" : str(e),
            "error_code" : SERVICE_UNAVAILABLE,
            "is_error" : True
        })
    except pymysql.MySQLError as e:
        if con:
            con.rollback()
        response_log("Database error while updating site", INTERNAL_SERVER_ERROR, True, str(e))
        return marshal_response_msg({
            "error_message" : "Database error while updating site",
            "error_details" : str(e),
            "error_code" : INTERNAL_SERVER_ERROR,
            "is_error" : True
        })
    except Exception:
        response_log("Unexpected error while get price by version", NOT_IMPLEMENTED, True, str(e))
        return marshal_response_msg({
            "error_message" : "Unexpected error while get price by version",
            "error_details" : str(e),
            "error_code" : NOT_IMPLEMENTED,
            "is_error" : True
        })
    finally:
        if con:
            con.close()