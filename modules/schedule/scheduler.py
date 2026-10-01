import os
from contextlib import contextmanager
from datetime import datetime

from data.structure.deactivation_combination import COMBINATION_COLUMNS as combination
from repository.mysql_connection import get_db_connection
from repository.query import (
    create_logger,
    deactivate_out_of_window_query,
    future_boundaries_query,
    price_fingerprint_query,
    reactivate_valid_combination_query,
)
from utils.log_error import logger
from utils.timezone import BUSINESS_TZ

PRICE_DB = os.getenv("DB_P_NAME")


def _now():
    return datetime.now(BUSINESS_TZ).replace(tzinfo=None)


@contextmanager
def _cursor():
    con = get_db_connection(PRICE_DB)
    cursor = con.cursor()
    try:
        yield con, cursor
    finally:
        cursor.close()
        con.close()


def refresh_price_status(now=None):
    now = now or _now()

    with _cursor() as (con, cursor):
        try:
            cursor.execute(deactivate_out_of_window_query(), (now, now))
            deactivated = cursor.rowcount

            cursor.execute(reactivate_valid_combination_query(combination), (now, now))
            reactivated = cursor.rowcount

            if deactivated or reactivated:
                cursor.execute(*create_logger(
                    "", f"{deactivated} expired item(s) deactivated, "
                        f"{reactivated} flag(s) updated for valid items."
                ))

            con.commit()
        except Exception:
            con.rollback()
            logger.exception("Error while refreshing price status")
            raise

    return {
        "status": "success",
        "message": "Price status refreshed",
        "checked_at": now.isoformat(sep=" "),
        "deactivated_rows": deactivated,
        "reactivated_rows": reactivated,
    }


def get_future_boundaries(now=None):
    now = now or _now()
    with _cursor() as (_, cursor):
        cursor.execute(future_boundaries_query(), (now, now, now, now))
        return [row["t"] for row in cursor.fetchall() if row["t"]]


def get_price_fingerprint():
    with _cursor() as (_, cursor):
        cursor.execute(price_fingerprint_query())
        row = cursor.fetchone() or {}
        return row.get("max_id"), row.get("max_updated"), row.get("total")