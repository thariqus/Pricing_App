from flask import request
import pymysql
from repository.mysql_connection import get_db_connection
import os
from repository.query import update_site_qry
from utils.log_response import _respond
from data.error_codes import INITIATING_FUNCTION, NOT_FOUND, SUCCESS, SERVICE_UNAVAILABLE, INTERNAL_SERVER_ERROR, BAD_REQUEST, NOT_IMPLEMENTED
from data.response import marshal_response_msg

PRICE_DB = os.getenv("DB_P_NAME")
SOURCE = "/api/update_site/"

def response_log(custom_message, code, error, response_message=None):
    return _respond(
        body={},
        custom_message=custom_message,
        ipaddress=request.remote_addr,
        response_message=response_message,
        source="repository",
        log_type="Edit Site",
        message_code=f"PP{code}",
        log_status=code,
        error=error
    )


def edit_one_site(site_id, data):
    con = None
    cursor = None

    response_log("Entered in edit site function", INITIATING_FUNCTION, False)
    try:
        # Database connection
        con = get_db_connection(PRICE_DB)
        cursor = con.cursor()

        if not site_id:
            response_log("Id is missing", BAD_REQUEST, True)
            return marshal_response_msg({
                "error_message" : "Id is missing",
                "error_details" : "Id is required but no id is given",
                "error_code" : BAD_REQUEST,
                "is_error" : True
            })


        if not data:
            response_log("Data is missing", BAD_REQUEST, True)
            return marshal_response_msg({
                "error_message" : "Data is missing",
                "error_details" : "Data is required but no data is given",
                "error_code" : BAD_REQUEST,
                "is_error" : True
            })

        # Get query and parameters
        update_query, params = update_site_qry(site_id, data)

        # Execute query
        cursor.execute(update_query, params)

        # Check whether the site exists
        if cursor.rowcount == 0:
            con.rollback()
            response_log("No changes made", NOT_FOUND, True)
            return marshal_response_msg({
                "error_message" : "No changes",
                "error_details" : "There is no updation is occured",
                "error_code" : BAD_REQUEST,
                "is_error" : True
            })

        response_log(f"Successfully edited {cursor.rowcount} site", SUCCESS, False)

        # Commit changes
        con.commit()

        response_log("Edit site completed", SUCCESS, False)
        return marshal_response_msg({
            "success_message" : "Site is updated successfully",
            "success_code" : SUCCESS,
            "source" : SOURCE,
            "is_error" : False
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
    except Exception as e:
        if con:
            con.rollback()
        response_log("Unexpected error while updating site", NOT_IMPLEMENTED, True, str(e))
        return marshal_response_msg({
            "error_message" : "Unexpected error while updating site",
            "error_details" : str(e),
            "error_code" : NOT_IMPLEMENTED,
            "is_error" : True
        })
    finally:
        if cursor:
            cursor.close()

        if con:
            con.close()
