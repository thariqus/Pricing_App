from repository.mysql_connection import get_db_connection
from repository.query import get_latest_version_id_query
from utils.log_error import logger

import os
from repository.mysql_connection import get_db_connection
from repository.query import get_version_record_count_query

PRICE_DB = os.getenv("DB_P_NAME")


def get_latest_version_id(db_name=PRICE_DB):
    con = None
    try:
        con = get_db_connection(db_name)
        with con.cursor() as cursor:
            cursor.execute(get_latest_version_id_query())
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


import os
from repository.mysql_connection import get_db_connection
from repository.query import get_version_record_count_query

PRICE_DB = os.getenv("DB_P_NAME")


def get_version_record_count(version_id):
    con = None
    try:
        con = get_db_connection(PRICE_DB)
        with con.cursor() as cursor:
            sql_query, params = get_version_record_count_query(version_id)
            cursor.execute(sql_query, params)
            row = cursor.fetchone()
            if not row:
                return 0
            return row["cnt"] if isinstance(row, dict) else row[0]
    finally:
        if con:
            con.close()