from flask import request
import pymysql
from repository.mysql_connection import get_db_connection
import os
from repository.query import delete_site_qry
from utils.log_response import _respond
from data.error_codes import INITIATING_FUNCTION, NOT_FOUND, SUCCESS, SERVICE_UNAVAILABLE, INTERNAL_SERVER_ERROR, NOT_IMPLEMENTED, BAD_REQUEST
from data.response import marshal_response_msg

PRICE_DB = os.getenv("DB_P_NAME")
SOURCE = "/api/delete_site/"

def response_log(custom_message, code, error, response_message=None):
    return _respond(
        body={},
        custom_message=custom_message,
        ipaddress=request.remote_addr,
        response_message=response_message,
        source="repository",
        log_type="Delete Site",
        message_code=f"PP{code}",
        log_status=code,
        error=error
    )


def delete_one_site(site_id):
    con = None
    cursor = None

    response_log("Entered in delete site function", INITIATING_FUNCTION, False)

    try:
        # Database connection
        con = get_db_connection(PRICE_DB)
        cursor = con.cursor()

        if not site_id:
            response_log("Id required but missing", BAD_REQUEST, True)
            return marshal_response_msg({
                "error_message" : "Id is missing",
                "error_details" : "Id is required but not given",
                "error_code" : BAD_REQUEST,
                "is_error" : True
            })

        # Get query and parameters
        sel_query, params = delete_site_qry(site_id)

        # Execute query
        cursor.execute(sel_query, params)

        # Check whether a row was deleted
        if cursor.rowcount == 0:
            response_log("Error in deleting site", NOT_FOUND, True)
            return marshal_response_msg({
                "error_message" : "Error in deletion",
                "error_details" : "Error occured when delete performed",
                "error_code" : INTERNAL_SERVER_ERROR,
                "is_error" : True
            })

        response_log(f"Successfully deleted {cursor.rowcount} site", SUCCESS, False)

        # Commit changes
        con.commit()

        response_log("Successfully completed site deletion", SUCCESS, False)

        return marshal_response_msg({
            "success_message" : "Site delete sucessfully",
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
        if con:
            con.rollback()
        response_log("Database error", INTERNAL_SERVER_ERROR, True, str(e))
        return marshal_response_msg({
            "error_message" : "Database error",
            "error_details" : str(e),
            "error_code" : INTERNAL_SERVER_ERROR,
            "is_error" : True
        })
    except Exception as e:
        if con:
            con.rollback()
        response_log("Unexpected error occure", NOT_IMPLEMENTED, True, str(e))
        return marshal_response_msg({
            "error_message" : "Unexpected error occure",
            "error_details" : str(e),
            "error_code" : NOT_IMPLEMENTED,
            "is_error" : True
        })
    finally:
        if cursor:
            cursor.close()

        if con:
            con.close()
