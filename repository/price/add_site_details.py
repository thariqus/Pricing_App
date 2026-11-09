from flask import request
from repository.mysql_connection import get_db_connection
import os
import pymysql
from repository.query import insert_site_settings
from utils.log_response import _respond
from data.error_codes import INITIATING_FUNCTION, BAD_REQUEST, SUCCESS, SERVICE_UNAVAILABLE, INTERNAL_SERVER_ERROR, NOT_IMPLEMENTED, CREATED
from data.response import marshal_response_msg

PRICE_DB = os.getenv("DB_P_NAME")
SOURCE = "/api/add_site_settings"

def response_log(custom_message, code, error, response_message=None):
    return _respond(
        body={},
        custom_message=custom_message,
        ipaddress=request.remote_addr,
        response_message=response_message,
        source="repository",
        log_type="Add site details",
        message_code=f"PP{code}",
        log_status=code,
        error=error
    )


def add_site_details(data):
    con = None
    cursor = None
    response_log("Entered in add site details function", INITIATING_FUNCTION, False)
    try:
        if not data:
            response_log("Given data i empty", BAD_REQUEST, True)
            return marshal_response_msg({
                "error_message" : "Given data is empty",
                "error_details" : "Please provide a valid data",
                "error_code" : BAD_REQUEST,
                "is_error" : True
            })
        # Database connection
        con = get_db_connection(PRICE_DB)
        cursor = con.cursor()
        # Execute query

        inserted_count = 0
        for sites in data['sites']:
            sql_query, params = insert_site_settings(sites)
            cursor.execute(sql_query, params)
            inserted_count += cursor.rowcount
        con.commit()

        if inserted_count == 0:
            return marshal_response_msg({
                "success_message" : f"{inserted_count} records created successfully",
                "success_code" : CREATED,
                "source" : SOURCE,
                "is_error" : False
            })
        response_log(f"{inserted_count} Sites created successfully", SUCCESS, False)

        response_log("Site setting completed successfully", SUCCESS, False)

        return marshal_response_msg({
            "success_message" : f"{inserted_count} records created successfully",
            "success_code" : CREATED,
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
        response_log("Database error while fetching prices", INTERNAL_SERVER_ERROR, True, str(e))
        return marshal_response_msg({
            "error_message" : "Database error while fetching prices",
            "error_details" : str(e),
            "error_code" : INTERNAL_SERVER_ERROR,
            "is_error" : True
        })
    except Exception as e:
        response_log("Unexpected error while fetching prices data", NOT_IMPLEMENTED, True, str(e))
        return marshal_response_msg({
            "error_message" : "Unexpected error while fetching prices data",
            "error_details" : str(e),
            "error_code" : NOT_IMPLEMENTED,
            "is_error" : True
        })
    finally:
        if cursor:
            cursor.close()
        if con:
            con.close()