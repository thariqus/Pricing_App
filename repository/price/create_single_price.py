from flask import request
import pymysql
from repository.mysql_connection import get_db_connection
from utils.log_response import _respond
from repository.query import insert_price_query, get_latest_version_id_query, insert_version_query, deactivate_combination_query, get_active_same_combination_query, deactivate_price_by_ids_query
from data.structure.deactivation_combination import COMBINATION_COLUMNS as combination
from data.error_codes import (
    INITIATING_FUNCTION,
    BAD_REQUEST,
    SUCCESS,
    SERVICE_UNAVAILABLE,
    INTERNAL_SERVER_ERROR,
    NOT_IMPLEMENTED,
    CREATED
)
import os
from datetime import datetime
from data.data_processing._clean_record import _clean_record
from data.data_processing._to_datetime import _to_datetime
from data.response import marshal_response_msg

SOURCE = "/api/items/create_singel_item_price"

PRICE_DB = os.getenv("DB_P_NAME")

def response_log(custom_message, code, error, response_message=None):
    return _respond(
        body={},
        custom_message=custom_message,
        ipaddress=request.remote_addr,
        response_message=response_message,
        source="repository",
        log_type="Create Single Price",
        message_code=f"PP{code}",
        log_status=code,
        error=error
    )

def create_single_price(datas):
    con = None
    cursor = None

    # Log function entry
    response_log("Entered in single item price function", INITIATING_FUNCTION, False)

    try:
        con = get_db_connection(PRICE_DB)
        cursor = con.cursor()
        inserted_count = 0
        is_future = False

        cursor.execute(get_latest_version_id_query())
        row = cursor.fetchone()

        latest = (
            row["version_id"] if isinstance(row, dict) else row[0]
        ) if row else None

        version_id = (latest or 0) + 1


        for data in datas:
            try:
                _clean_record(data)
            except ValueError as e:
                response_log("Data processing error", SERVICE_UNAVAILABLE, True, str(e))
                return ("", {"error" : True, "error_code" : INTERNAL_SERVER_ERROR})
            
            data['id'] = ""
            sql_query, params = get_active_same_combination_query(data, combination)
            cursor.execute(sql_query, params)
            active_rows = cursor.fetchall()

            is_future = True if _to_datetime(data['starting_date']) < datetime.now() else False
            if active_rows:
                latest_rows = [
                    row for row in active_rows
                    if row['active'] == 1
                ]
                ids_to_deactivate = []
                if latest_rows:
                    is_future = True if (
                        (latest_rows[0]['starting_date'] <= _to_datetime(data['starting_date']) <= datetime.now()) 
                        or 
                        (_to_datetime(data['starting_date']) < datetime.now())) else False
                    ids_to_deactivate = [
                        row["id"]
                        for row in active_rows
                        if is_future or row['id'] != latest_rows[0]['id']
                    ]
                else:
                    is_future = True if _to_datetime(data['starting_date']) < datetime.now() else False


                if ids_to_deactivate:
                    sql_query, params = deactivate_price_by_ids_query(ids_to_deactivate)
                    cursor.execute(sql_query, params)
            # 2. new price -> active only if it has started
            data["active"] = 1 if is_future else 0
            data["version_id"] = version_id

            sql_query, params = insert_price_query(data)
            cursor.execute(sql_query, params)
            inserted_count += 1

        if not inserted_count:
            con.rollback()
            response_log("Price could not be created", INTERNAL_SERVER_ERROR, True)
            return ("", {"error" : True, "error_code" : INTERNAL_SERVER_ERROR})

        version_sql, version_params = insert_version_query({
            "id": version_id,
            "file_name": "",
            "record_count": 1,
        })

        cursor.execute(version_sql, version_params)
        con.commit()

        response_log("Price created successfully", SUCCESS, False)

        return (inserted_count, {"error" : False, "error_code" : SUCCESS})

    except ConnectionError as e:
        mysql_error_code = e.args[0] if e.args else None
        http_status = SERVICE_UNAVAILABLE if mysql_error_code in (2002, 2003, 2006, 2013) else INTERNAL_SERVER_ERROR

        response_log("Databse connection error, unable to connect database", http_status, True, str(e))

        return ("", {"error" : True, "error_code" : http_status})
    
    except pymysql.MySQLError as e:
        mysql_error_code = e.args[0] if e.args else None
        http_status = SERVICE_UNAVAILABLE if mysql_error_code in (2002, 2003, 2006, 2013) else INTERNAL_SERVER_ERROR

        response_log("Database error while creating prices", http_status, True, str(e))
        
        return ("", {"error" : True, "error_code" : http_status})
    
    except Exception as e:
        response_log("Unexpected error while creating prices data", NOT_IMPLEMENTED, True, str(e))
        
        return ("", {"error" : True, "error_code" : NOT_IMPLEMENTED})

    finally:
        if cursor:
            cursor.close()
        if con:
            con.close()
