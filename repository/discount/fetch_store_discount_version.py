from repository.mysql_connection import get_db_connection
from repository.query import get_latest_version_id_query_discount
from utils.log_error import logger

import os
from repository.mysql_connection import get_db_connection
from repository.query import get_version_record_count_query_discount

DISCOUNT_DB = os.getenv("DB_D_NAME")


def get_latest_version_id():
    con = None
    try:
        con = get_db_connection(DISCOUNT_DB)
        with con.cursor() as cursor:
            cursor.execute(get_latest_version_id_query_discount())
            row = cursor.fetchone()
        if not row:
            return None
        return row["version_id"] if isinstance(row, dict) else row[0]
    except Exception:
        logger.exception("Failed to get latest version id")
        return None
    finally:
        if con:
            con.close()


def get_version_record_count(version_id):
    con = None
    try:
        con = get_db_connection(DISCOUNT_DB)
        with con.cursor() as cursor:
            sql_query, params = get_version_record_count_query_discount(version_id)
            cursor.execute(sql_query, params)
            row = cursor.fetchone()
            if not row:
                return 0
            return row["cnt"] if isinstance(row, dict) else row[0]
    finally:
        if con:
            con.close()