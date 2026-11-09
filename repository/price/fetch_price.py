from flask import request
from repository.mysql_connection import get_db_connection
import os
from repository.query import select_all_prices
import pymysql
from utils.log_response import _respond
from data.response import marshal_response_msg
from data.error_codes import INITIATING_FUNCTION, BAD_REQUEST, SUCCESS, SERVICE_UNAVAILABLE, INTERNAL_SERVER_ERROR, NOT_FOUND

PRICE_DB = os.getenv("DB_P_NAME")
SOURCE = "/api/items/fetch_all_item_prices"

def response_log(custom_message, code, error, response_message=None):
    return _respond(
        body={},
        custom_message=custom_message,
        ipaddress=request.remote_addr,
        response_message=response_message,
        source="repository",
        log_type="Fetch all prices",
        message_code=f"PP{code}",
        log_status=code,
        error=error
    )


def fetch_all_prices():
    con = None
    cursor = None
    response_log("Enter into fetch all price", INITIATING_FUNCTION, False)
    try:
        # Get pagination values
        page = request.args.get("page", default=1, type=int)
        limit = request.args.get("limit", default=100, type=int)
        # Validate pagination
        if page < 1:
            response_log("Page must be greater than 0", BAD_REQUEST, True)
            return marshal_response_msg({
                "error_message" : "Page value is 0",
                "error_details" : "The page value should be minimum 1 not to be 0, give a valid page value",
                "error_code" : BAD_REQUEST,
                "source" : SOURCE,
                "is_error" : True
            })
        if limit < 1 or limit > 100:
            response_log("Limit must be between 1 and 100", BAD_REQUEST, True)
            return marshal_response_msg({
                "error_message" : "Limit must be between 1 and 100",
                "error_details" : "The limit value should be minimum 1 and maximum 100, give a valid limit",
                "error_code" : BAD_REQUEST,
                "source" : SOURCE,
                "is_error" : True
            })
        
        # Database connection
        con = get_db_connection(PRICE_DB)
        cursor = con.cursor()
        # Execute query
        sel_query, count_query, params = select_all_prices(page, limit)
        cursor.execute(sel_query, params)
        price_data = cursor.fetchall()
        cursor.execute(count_query)
        total_records = cursor.fetchone()["total"]
        
        if not price_data:
            response_log("No pricing data found", BAD_REQUEST, True)
            return marshal_response_msg({
                "success_message" : "No data founded",
                "success_code" : NOT_FOUND,
                "source" : SOURCE,
                "is_error" : False,
                "custom_field" : {
                    "page" : page,
                    "limit" : limit,
                    "total_records" : total_records
                }
            })
        

        response_log("Price selected successfully", SUCCESS, False)
        return marshal_response_msg({
            "data" : price_data,
            "success_message" : f"Successfully selected {total_records} records",
            "success_code" : SUCCESS,
            "source" : SOURCE,
            "custom_field" : {
                "page" : page,
                "limit" : limit,
                "total_records" : total_records
            },
            "is_error" : False
        })
    except ConnectionError as e:
        response_log("Database connection error", SERVICE_UNAVAILABLE, True, str(e))
        return marshal_response_msg({
            "error_message" : "Database connection error",
            "error_details" : str(e),
            "error_code" : SERVICE_UNAVAILABLE,
            "source" : SOURCE,
            "is_error" : True
        })
    except pymysql.MySQLError as e:
        response_log("Database error while fetching prices", INTERNAL_SERVER_ERROR, True, str(e))
        return marshal_response_msg({
            "error_message" : "Database error while fetching prices",
            "error_details" : str(e),
            "error_code" : INTERNAL_SERVER_ERROR,
            "source" : SOURCE,
            "is_error" : True
        })
    except Exception as e:
        response_log("Unexpected error while fetching prices data", INTERNAL_SERVER_ERROR, True, str(e))
        return marshal_response_msg({
            "error_message" : "Unexpected error while fetching prices data",
            "error_details" : str(e),
            "error_code" : INTERNAL_SERVER_ERROR,
            "source" : SOURCE,
            "is_error" : True
        })
    finally:
        if cursor:
            cursor.close()
        if con:
            con.close()