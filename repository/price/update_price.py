from flask import request
from repository.mysql_connection import get_db_connection
import os
from repository.query import check_price_exists, update_price
import pymysql
from utils.log_response import _respond
from data.error_codes import INITIATING_FUNCTION, NOT_FOUND, SUCCESS, SERVICE_UNAVAILABLE, INTERNAL_SERVER_ERROR, BAD_REQUEST, NOT_IMPLEMENTED
from data.response import marshal_response_msg

PRICE_DB = os.getenv("DB_P_NAME")
SOURCE = "/api/items/update_item_prices/"

def response_log(custom_message, code, error, response_message=None):
    return _respond(
        body={},
        custom_message=custom_message,
        ipaddress=request.remote_addr,
        response_message=response_message,
        source="repository",
        log_type="Update price data",
        message_code=f"PP{code}",
        log_status=code,
        error=error
    )


def update_price_data(data):
    con = None
    cursor = None
    response_log("Enter into update price data function", INITIATING_FUNCTION, False)
    try:
        if not data:
            response_log("No data found", BAD_REQUEST, True)
            return marshal_response_msg({
                "error_message" : "No data found",
                "error_details" : "Data is required, but not found",
                "error_code" : BAD_REQUEST,
                "is_error" : True
            })
        con = get_db_connection(PRICE_DB)
        cursor = con.cursor()
        updated_records = []
        failed_records = []
        for record in data:
            price_id = record.get("id")
            if not price_id:
                response_log("Price id not found", NOT_FOUND, True)
                failed_records.append({
                    "data": record,
                    "message": "Price ID is required"
                })
                continue
            check_query, check_params = check_price_exists(price_id)
            cursor.execute(
                check_query,
                check_params
            )
            existing_price = cursor.fetchone()
            if not existing_price:
                response_log("Price record not found", NOT_FOUND, True)
                failed_records.append({
                    "id": price_id,
                    "message": "Price record not found"
                })
                continue
            update_data = {
                key: value
                for key, value in record.items()
                if key != "id"
            }
            if not update_data:
                response_log("No fields to updated", NOT_FOUND, True)
                failed_records.append({
                    "id": price_id,
                    "message": "No fields to update"
                })
                continue
            sql_query, params = update_price(
                price_id,
                update_data
            )
            cursor.execute(
                sql_query,
                params
            )
            if cursor.rowcount > 0:
                response_log("Price Updated..", SUCCESS, False)
            updated_records.append({
                "id": price_id
            })
        con.commit()
        response_log("Update price completed", SUCCESS, False)
        return marshal_response_msg({
            "data" : updated_records,
            "success_message" : "Price update completed",
            "success_code" : SUCCESS,
            "source" : SOURCE,
            "is_error" : False,
            "custom_field" : {
                "updated_count": len(updated_records),
                "failed_count": len(failed_records),
                "failed": failed_records
            }
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
        response_log("Database error while fetching update prices", INTERNAL_SERVER_ERROR, True, str(e))
        return marshal_response_msg({
            "error_message" : "Database error while fetching update prices",
            "error_details" : str(e),
            "error_code" : INTERNAL_SERVER_ERROR,
            "is_error" : True
        })
    except Exception as e:
        response_log("Unexpected error while fetching update prices data", NOT_IMPLEMENTED, True, str(e))
        return marshal_response_msg({
            "error_message" : "Unexpected error while fetching update prices data",
            "error_details" : str(e),
            "error_code" : NOT_IMPLEMENTED,
            "is_error" : True
        })
    finally:
        if cursor:
            cursor.close()
        if con:
            con.close()
