from flask import request
from repository.mysql_connection import get_db_connection
import os
from repository.query import get_ho_version_count_data
import pymysql
from utils.log_response import _respond
from data.error_codes import INITIATING_FUNCTION, SUCCESS, SERVICE_UNAVAILABLE, INTERNAL_SERVER_ERROR

PRICE_DB = os.getenv("DB_P_NAME")

def response_log(custom_message, code, error, response_message=None):
    return _respond(
        body={},
        custom_message=custom_message,
        ipaddress=request.remote_addr,
        response_message=response_message,
        source="repository",
        log_type="Get HO version count",
        message_code=f"PP{code}",
        log_status=code,
        error=error
    )

def get_ho_version_count(version_id, site_code):
    con = None
    cursor = None
    response_log("Enter into get ho version count function", INITIATING_FUNCTION, False)
    try:
        # Database connection
        con = get_db_connection(PRICE_DB)
        cursor = con.cursor()
        # Execute query

        rep_qry, rep_params = get_ho_version_count_data(version_id, site_code)
        cursor.execute(rep_qry, rep_params)
        row = cursor.fetchall()

        response_log("Get HO version count completed", SUCCESS, False)

        return row
    except ConnectionError as e:
        return response_log("Database connection error", SERVICE_UNAVAILABLE, True, str(e))
    except pymysql.MySQLError as e:
        return response_log("Database error while fetching ho version count", INTERNAL_SERVER_ERROR, True, str(e))
    except Exception as e:
        return response_log("Unexpected error while fetching ho version count", INTERNAL_SERVER_ERROR, True, str(e))
    finally:
        if cursor:
            cursor.close()
        if con:
            con.close()