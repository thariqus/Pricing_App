from flask import request
from repository.query import filter_prices
from repository.mysql_connection import get_db_connection
import os
import pymysql
from utils.log_response import _respond
from data.error_codes import INITIATING_FUNCTION, BAD_REQUEST, SUCCESS, SERVICE_UNAVAILABLE, INTERNAL_SERVER_ERROR, NOT_IMPLEMENTED
from data.response import marshal_response_msg

PRICE_DB = os.getenv("DB_P_NAME")
SOURCE = "/api/items/filter_item_prices"

def response_log(custom_message, code, error, response_message=None):
    return _respond(
        body={},
        custom_message=custom_message,
        ipaddress=request.remote_addr,
        response_message=response_message,
        source="repository",
        log_type="Filter price data",
        message_code=f"PP{code}",
        log_status=code,
        error=error
    )

def filter_price_data(data):
    con = None
    cursor = None
    response_log("Enter into filter price data function", INITIATING_FUNCTION, False)
    try:
        if data is None:
            response_log("Request must contain valid JSON", BAD_REQUEST, True)
            return marshal_response_msg({
                "error_message" : "Request must contain valid JSON",
                "error_details" : "Given filter is empty, please provide a valid filter",
                "error_code" : BAD_REQUEST,
                "is_error" : True
            })
        page  = int(data.get("page") or 1)
        limit = int(data.get("limit") or 500)
 
        if page < 1 or limit < 1 or limit > 500:
            response_log("Invalid page or limit", BAD_REQUEST, True)
            return marshal_response_msg({
                "error_message" : "Invalid page or limit",
                "error_details" : "Given page or limit is invalid, check it and provide a valid page and limit",
                "error_code" : BAD_REQUEST,
                "is_error" : True
            })
        con = get_db_connection(PRICE_DB)
        cursor = con.cursor()
        sql_query, count_query, params, count_params = filter_prices(
            data, page, limit
        )
        cursor.execute(sql_query, params)
        price_data = cursor.fetchall()
        cursor.execute(count_query, count_params)
        total = cursor.fetchone()["total"]
        for row in price_data:
            for field in ("starting_date", "ending_date"):
                value = row.get(field)
                if value is not None:
                    row[field] = value.strftime("%Y-%m-%d %H:%M:%S")
        response_log("Filter pricing data completed", SUCCESS, False)
        return marshal_response_msg({
            "data" : price_data,
            "success_message" : "Successfully select price data",
            "success_code" : SUCCESS,
            "source" : SOURCE,
            "is_error" : False,
            "custom_field" : {
                "page" : page,
                "limit" : limit,
                "total" : total
            }
        })
    except ConnectionError as e:
        response_log("Database connection error", SERVICE_UNAVAILABLE, True, str(e))
        return marshal_response_msg({
            "error_message" : "Database connection error",
            "error_details" : str(e),
            "error_code" : SERVICE_UNAVAILABLE,
            "is_error" : True
        })
    except pymysql.MySQLError as e:
        response_log("Database error while filtering prices", INTERNAL_SERVER_ERROR, True, str(e))
        return marshal_response_msg({
            "error_message" : "Database error while filtering prices",
            "error_details" : str(e),
            "error_code" : INTERNAL_SERVER_ERROR,
            "is_error" : True
        })
    except Exception as e:
        response_log("Unexpected error while filtering prices data", NOT_IMPLEMENTED, True, str(e))
        return marshal_response_msg({
            "error_message" : "Unexpected error while filtering prices data",
            "error_details" : str(e),
            "error_code" : NOT_IMPLEMENTED,
            "is_error" : True
        })
    finally:
        if cursor:
            cursor.close()
        if con:
            con.close()