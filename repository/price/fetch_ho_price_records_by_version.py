import os
from repository.query import get_prices_from_version_query
from repository.mysql_connection import get_db_connection
from utils.log_error import logger


def get_prices_from_version(version_id, site_code, skip=0):
    con = None
    try:
        con = get_db_connection(os.getenv("DB_P_NAME"))
        with con.cursor() as cursor:
            sql_query, params = get_prices_from_version_query(version_id, site_code, skip)
            cursor.execute(sql_query, params)
            return cursor.fetchall()
    except Exception:
        logger.exception("Failed to get prices from version %s", version_id)
        return []
    finally:
        if con:
            con.close()