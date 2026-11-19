from flask import request
from repository.mysql_connection import get_db_connection
import os
from repository.query import check_price_exists, update_price, get_latest_version_id_query, insert_version_query
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
        con = get_db_connection(PRICE_DB)
        cursor = con.cursor()
        updated_records = []
        failed_records = []

        cursor.execute(get_latest_version_id_query())
        row = cursor.fetchone()

        latest = (
            row["version_id"] if isinstance(row, dict) else row[0]
        ) if row else None

        version_id = (latest or 0) + 1

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
                **{key: value for key, value in record.items() if key != "id"},
                "version_id": version_id
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

        version_sql, version_params = insert_version_query({
            "id": version_id,
            "file_name": "",
            "record_count": cursor.rowcount,
        })

        cursor.execute(version_sql, version_params)
        con.commit()
        response_log("Update price completed", SUCCESS, False)
        return ({
            "data" : updated_records,
            "updated_count": len(updated_records),
            "failed_count": len(failed_records),
            "failed": failed_records
        },
        {"error" : False, "error_code" : SUCCESS})
        
    except ConnectionError as e:
        mysql_error_code = e.args[0] if e.args else None
        http_status = SERVICE_UNAVAILABLE if mysql_error_code in (2002, 2003, 2006, 2013) else INTERNAL_SERVER_ERROR

        response_log("Databse connection error, unable to connect database", http_status, True, str(e))

        return ("", {
            "error" : True, 
            "error_code" : http_status})
    
    except pymysql.MySQLError as e:
        mysql_error_code = e.args[0] if e.args else None
        http_status = SERVICE_UNAVAILABLE if mysql_error_code in (2002, 2003, 2006, 2013) else INTERNAL_SERVER_ERROR

        response_log("Database error while update price", http_status, True, str(e))
        
        return ("", {
            "error" : True, 
            "error_code" : http_status})
    
    except Exception as e:
        response_log("Unexpected error while update price", NOT_IMPLEMENTED, True, str(e))
        
        return ("", {
            "error" : True, 
            "error_code" : NOT_IMPLEMENTED})
    finally:
        if cursor:
            cursor.close()
        if con:
            con.close()
