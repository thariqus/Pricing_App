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
)
from data.error_codes import BAD_REQUEST, SUCCESS, SERVICE_UNAVAILABLE, INTERNAL_SERVER_ERROR
from data.response import marshal_response_msg

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
    )

def store_create_price(records):
    con = None
    try:
        if not records:
            return marshal_response_msg({
                "error_message" : "No Records found",
                "error_details" : "Records is required, but not given",
                "error_code" : BAD_REQUEST,
                "is_error" : True
            })

        con = get_db_connection(PRICE_DB)
        con.autocommit(False)

        with con.cursor() as cursor:
            cursor.execute(*get_max_price_id_query())
            row = cursor.fetchone()
            after_id = row["max_id"] if isinstance(row, dict) else row[0]

            insert_sql = store_insert_price_query()
            for i in range(0, len(records), BATCH_SIZE):
                batch = records[i:i + BATCH_SIZE]
                cursor.executemany(insert_sql, [_row_params(r) for r in batch])

            cursor.execute(*store_activate_started_query(after_id))
            cursor.execute(*store_deactivate_old_query(after_id))
            deactivated = cursor.rowcount
            cursor.execute(*store_upsert_versions_query(after_id))

        con.commit()   # all rows, activations, deactivations and versions together
        
        return marshal_response_msg({
            "success_message" : "Successfully created",
            "success_code" : SUCCESS,
            "source" : SOURCE,
            "is_error" : False,
            "custom_field" : {
                "inserted" : len(records),
                "deactivated" : deactivated
            }
        })

    except ConnectionError as e:
        return marshal_response_msg({
        "error_message" : "Database connection error",
        "error_details" : str(e),
        "error_code" : SERVICE_UNAVAILABLE,
        "is_error" : True
        })
    except Exception:
        return marshal_response_msg({
            "error_message" : "Unexpected error while store create price",
            "error_details" : str(e),
            "error_code" : INTERNAL_SERVER_ERROR,
            "is_error" : True
            })
    finally:
        if con:
            con.close()