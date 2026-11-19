import os
from flask import request
from repository.mysql_connection import get_db_connection
from utils.file_path import upload_price_directory
from repository.query import (
    insert_price_query,
    deactivate_combination_query,
    get_latest_version_id_query,   # version
    insert_version_query,          # version
    get_active_same_combination_query,
    deactivate_price_by_ids_query
)

from data.structure.deactivation_combination import COMBINATION_COLUMNS as combination
import pymysql
from datetime import datetime
from data.data_processing._clean_record import _clean_record
from data.data_processing._to_datetime import _to_datetime
from utils.log_response import _respond
from data.error_codes import INITIATING_FUNCTION, SUCCESS, SERVICE_UNAVAILABLE, INTERNAL_SERVER_ERROR, BAD_REQUEST, CREATED, NOT_IMPLEMENTED
from data.response import marshal_response_msg

PRICE_DB = os.getenv("DB_P_NAME")
SOURCE = "/api/items/store_csv_uploads"

def response_log(custom_message, code, error, response_message=None):
    return _respond(
        body={},
        custom_message=custom_message,
        ipaddress=request.remote_addr,
        response_message=response_message,
        source="repository",
        log_type="Create HO price",
        message_code=f"PP{code}",
        log_status=code,
        error=error
    )

def ho_create_price(records, file, invalid_data):
    con = None
    cursor = None
    current = None
    response_log("Enter into get ho price create function", INITIATING_FUNCTION, False)

    if invalid_data is None:
        invalid_data = []
        
    try:
        con = get_db_connection(PRICE_DB)
        cursor = con.cursor()

        inserted = 0
        deactivated = 0
        is_future = False

        cursor.execute(get_latest_version_id_query())
        row = cursor.fetchone()
        latest = (row["version_id"] if isinstance(row, dict) else row[0]) if row else None
        version_id = (latest or 0) + 1

        now = datetime.now()

        for data in records:
            current = data

            if not isinstance(data, dict) or not data.get("item_no"):
                continue

            # 0. validate BEFORE touching the DB, so a bad row never deactivates a good price
            original = dict(data)
            try:
                _clean_record(data)
            except ValueError as e:
                invalid_data.append({**original, "reason": str(e)})
                continue

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
            data["version_id"] = version_id   # version

            sql_query, params = insert_price_query(data)
            try:
                cursor.execute(sql_query, params)
            except pymysql.err.DataError:
                raise
            inserted += 1

        current = None

        if inserted:
            response_log("HO price inserted complete", SUCCESS, False)
            version_sql, version_params = insert_version_query({
                "id": version_id,
                "file_name": file.filename if file else "",
                "record_count": inserted,
            })
            cursor.execute(version_sql, version_params)

        if file:
            file_path = os.path.join(upload_price_directory, file.filename)
            file.save(file_path)

        con.commit()   # deactivations + inserts land together

        response_log("HO price insert completed", SUCCESS, False)
        return (
            {
                "count": inserted,
                "deactivated": deactivated,
                "InvalidData": invalid_data
            },
            {"error" : False, "error_code" : CREATED}
        )

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

        response_log("Database error while create price", http_status, True, str(e))
        
        return ("", {
            "error" : True, 
            "error_code" : http_status})
    
    except Exception as e:
        response_log("Unexpected error while create price", NOT_IMPLEMENTED, True, str(e))
        
        return ("", {
            "error" : True, 
            "error_code" : NOT_IMPLEMENTED})

    finally:
        if cursor:
            cursor.close()
        if con:
            con.close()