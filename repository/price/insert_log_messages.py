from flask import request
from repository.mysql_connection import get_db_connection
from repository.query import insert_log_message_query
import pymysql
import os
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
        log_type="Insert Log message",
        message_code=f"PP{code}",
        log_status=code,
        error=error
    )


def insert_log_messages(c_message, r_message, source, m_code, l_status):
    con = None
    cursor = None
    response_log("Enter into get insert log message function", INITIATING_FUNCTION, False)
    try:
        con = get_db_connection(PRICE_DB)
        cursor = con.cursor()
        sql_query, params = insert_log_message_query(c_message, r_message, source, m_code, l_status)
        cursor.execute(
            sql_query,
            params
        )
        inserted_id = cursor.lastrowid
        if inserted_id:
            response_log("Insert log message inserted", SUCCESS, False)
        con.commit()

        response_log("Insert log message inserted complete", SUCCESS, False)
        return {
            "status": "success",
            "message": "Price created successfully",
            "id": inserted_id
        }
    except ConnectionError as e:
        return response_log("Database connection error", SERVICE_UNAVAILABLE, True, str(e))
    except pymysql.MySQLError as e:
        return response_log("Database error while insert log message", INTERNAL_SERVER_ERROR, True, str(e))
    except Exception as e:
        return response_log("Unexpected error while insert log message", INTERNAL_SERVER_ERROR, True, str(e))
    finally:
        if cursor:
            cursor.close()
        if con:
            con.close()