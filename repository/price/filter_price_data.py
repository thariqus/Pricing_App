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
        page  = int(data.get("page") or 1)
        limit = int(data.get("limit") or 500)
 
        if page < 1 or limit < 1 or limit > 500:
            response_log("Invalid page or limit", BAD_REQUEST, True)
            return ("", {
                "error" : True, 
                "error_code" : BAD_REQUEST,
                "page" : page,
                "limit" : limit,
                "total" : ""
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
        return ({
            "data" : price_data,
            "page" : page,
            "limit" : limit,
            "total" : total
            }
            , {"error" : False, "error_code" : SUCCESS})
        
    except ConnectionError as e:
        mysql_error_code = e.args[0] if e.args else None
        http_status = SERVICE_UNAVAILABLE if mysql_error_code in (2002, 2003, 2006, 2013) else INTERNAL_SERVER_ERROR

        response_log("Databse connection error, unable to connect database", http_status, True, str(e))

        return ("", {
            "error" : True, 
            "error_code" : http_status,
            "page" : page,
            "limit" : limit,
            "total" : ""})
    
    except pymysql.MySQLError as e:
        mysql_error_code = e.args[0] if e.args else None
        http_status = SERVICE_UNAVAILABLE if mysql_error_code in (2002, 2003, 2006, 2013) else INTERNAL_SERVER_ERROR

        response_log("Database error while filter all prices", http_status, True, str(e))
        
        return ("", {
            "error" : True, 
            "error_code" : http_status,
            "page" : page,
            "limit" : limit,
            "total" : ""})
    
    except Exception as e:
        response_log("Unexpected error while filter all price", NOT_IMPLEMENTED, True, str(e))
        
        return ("", {
            "error" : True, 
            "error_code" : NOT_IMPLEMENTED,
            "page" : page,
            "limit" : limit,
            "total" : ""})
    finally:
        if cursor:
            cursor.close()
        if con:
            con.close()