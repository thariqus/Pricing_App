import os
from datetime import datetime
from email.utils import parsedate_to_datetime
from repository.mysql_connection import get_db_connection
from repository.query import (
    STORE_DISCOUNT_COLUMNS,
    get_max_discount_id_query,
    get_latest_discount_version_id_query,
    get_discount_version_record_count_query,
    store_insert_discount_query,
    store_activate_started_discount_query,
    store_deactivate_old_discount_query,
    store_upsert_discount_versions_query,
)
from utils.log_error import logger

DISCOUNT_DB = os.getenv("DB_D_NAME")
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
    # The HO row's id becomes ho_id here; the store assigns its own id
    record = {**record, "ho_id": record.get("id")}
    return tuple(
        _db_datetime(record.get(col)) if col in DATE_COLUMNS else record.get(col)
        for col in STORE_DISCOUNT_COLUMNS
    )


def get_store_latest_discount_version():
    con = None
    try:
        con = get_db_connection(DISCOUNT_DB)
        with con.cursor() as cursor:
            cursor.execute(get_latest_discount_version_id_query())
            row = cursor.fetchone()
        if not row:
            return 0
        return int((row["version_id"] if isinstance(row, dict) else row[0]) or 0)
    finally:
        if con:
            con.close()


def get_store_discount_version_count(version_id):
    con = None
    try:
        con = get_db_connection(DISCOUNT_DB)
        with con.cursor() as cursor:
            cursor.execute(*get_discount_version_record_count_query(version_id))
            row = cursor.fetchone()
        if not row:
            return 0
        return row["cnt"] if isinstance(row, dict) else row[0]
    finally:
        if con:
            con.close()


def store_create_discount(records):
    if not records:
        return {"inserted": 0, "deactivated": 0}

    con = None
    try:
        con = get_db_connection(DISCOUNT_DB)
        con.autocommit(False)

        with con.cursor() as cursor:
            cursor.execute(*get_max_discount_id_query())
            row = cursor.fetchone()
            after_id = row["max_id"] if isinstance(row, dict) else row[0]

            insert_sql = store_insert_discount_query()
            for i in range(0, len(records), BATCH_SIZE):
                batch = records[i:i + BATCH_SIZE]
                cursor.executemany(insert_sql, [_row_params(r) for r in batch])

            cursor.execute(*store_activate_started_discount_query(after_id))
            cursor.execute(*store_deactivate_old_discount_query(after_id))
            deactivated = cursor.rowcount
            cursor.execute(*store_upsert_discount_versions_query(after_id))

        con.commit()   # all rows, activations, deactivations and versions together
        logger.info("Discount replication: %s inserted, %s deactivated", len(records), deactivated)
        return {"inserted": len(records), "deactivated": deactivated}

    except Exception:
        if con:
            con.rollback()   # nothing from this batch is kept
        logger.exception("Discount replication insert failed, batch rolled back")
        raise
    finally:
        if con:
            con.close()
