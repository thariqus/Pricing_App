import os
from datetime import datetime
from email.utils import parsedate_to_datetime
from repository.mysql_connection import get_db_connection
from repository.query import (
    STORE_PRICE_COLUMNS,
    get_max_price_id_query,
    store_insert_price_query,
    store_activate_started_query,
    store_deactivate_old_query,
    store_upsert_versions_query,
    get_active_same_combination_query,
    deactivate_price_by_ids_query,
)
from data.error_codes import SUCCESS, SERVICE_UNAVAILABLE, INTERNAL_SERVER_ERROR, NOT_IMPLEMENTED
import pymysql
from data.structure.deactivation_combination import COMBINATION_COLUMNS as combination
from data.data_processing._to_datetime import _to_datetime

PRICE_DB = os.getenv("DB_P_NAME")
BATCH_SIZE = 1000
DATE_COLUMNS = ("starting_date", "ending_date")
SOURCE = ""


def _db_datetime(value):
    if not value or isinstance(value, datetime):
        return value
    try:
        return parsedate_to_datetime(value).replace(tzinfo=None)   # jsonify format
    except (TypeError, ValueError):
        return value

def _row_params(record):
    return tuple(
        _db_datetime(record.get(col)) if col in DATE_COLUMNS else record.get(col)
        for col in STORE_PRICE_COLUMNS
    ) + (record.get("active", 0),)

def check_combination(cursor, data):
    data['id'] = ""
    sql_query, params = get_active_same_combination_query(data, combination)
    cursor.execute(sql_query, params)
    active_rows = cursor.fetchall()

    if active_rows:
        ids_to_deactivate = [
            row["id"]
            for row in active_rows
        ]
        if ids_to_deactivate:
            sql_query, params = deactivate_price_by_ids_query(ids_to_deactivate)
            cursor.execute(sql_query, params)

def store_create_price(records):
    con = None
    try:
        con = get_db_connection(PRICE_DB)
        con.autocommit(False)

        with con.cursor() as cursor:
            cursor.execute(*get_max_price_id_query())
            row = cursor.fetchone()
            after_id = row["max_id"] if isinstance(row, dict) else row[0]

            insert_sql = store_insert_price_query()
            for i in range(0, len(records), BATCH_SIZE):
                batch = records[i:i + BATCH_SIZE]
                [check_combination(cursor, data) for data in batch]
                cursor.executemany(insert_sql, [_row_params(r) for r in batch])

            # cursor.execute(*store_activate_started_query(after_id))
            # cursor.execute(*store_deactivate_old_query(after_id))
            # deactivated = cursor.rowcount
            cursor.execute(*store_upsert_versions_query(after_id))

        con.commit()   # all rows, activations, deactivations and versions together

        return ({
            "inserted" : len(records),
            # "deactivated" : deactivated
        },
        {"error" : False, "error_code" : SUCCESS})

    except ConnectionError as e:
        mysql_error_code = e.args[0] if e.args else None
        http_status = SERVICE_UNAVAILABLE if mysql_error_code in (2002, 2003, 2006, 2013) else INTERNAL_SERVER_ERROR

        return (
            {
            "inserted" : 0,
            "deactivated" : 0
            }, {
            "error" : True, 
            "error_code" : http_status})
    
    except pymysql.MySQLError as e:
        mysql_error_code = e.args[0] if e.args else None
        http_status = SERVICE_UNAVAILABLE if mysql_error_code in (2002, 2003, 2006, 2013) else INTERNAL_SERVER_ERROR

        return (
            {
            "inserted" : 0,
            "deactivated" : 0
            }, {
            "error" : True, 
            "error_code" : http_status})
    
    except Exception as e:

        return (
            {
            "inserted" : 0,
            "deactivated" : 0
            }, {
            "error" : True, 
            "error_code" : NOT_IMPLEMENTED})
    finally:
        if con:
            con.close()