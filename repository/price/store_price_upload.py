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
from utils.log_error import logger

PRICE_DB = os.getenv("DB_P_NAME")
BATCH_SIZE = 1000
DATE_COLUMNS = ("starting_date", "ending_date")


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
    if not records:
        return {"inserted": 0, "deactivated": 0}

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
                cursor.executemany(insert_sql, [_row_params(r) for r in batch])

            cursor.execute(*store_activate_started_query(after_id))
            cursor.execute(*store_deactivate_old_query(after_id))
            deactivated = cursor.rowcount
            cursor.execute(*store_upsert_versions_query(after_id))

        con.commit()   # all rows, activations, deactivations and versions together
        logger.info("Replication: %s inserted, %s deactivated", len(records), deactivated)
        return {"inserted": len(records), "deactivated": deactivated}

    except Exception:
        if con:
            con.rollback()   # nothing from this batch is kept
        logger.exception("Replication insert failed, batch rolled back")
        raise
    finally:
        if con:
            con.close()