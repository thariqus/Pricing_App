from repository.query import get_prices_from_version_query
from repository.mysql_connection import get_db_connection
from utils.log_error import logger


def get_prices_from_version(version_id):
    con = None
    try:
        con = get_db_connection("PRICING_DATABASE")
        with con.cursor() as cursor:
            sql_query, params = get_prices_from_version_query(version_id)
            cursor.execute(sql_query, params)
            rows = cursor.fetchall()
        print(f"Records from version {version_id}: {len(rows)}", flush=True)
        for row in rows:
            print(row, flush=True)
        return rows
    except Exception:
        logger.exception("Failed to get prices from version %s", version_id)
        return []
    finally:
        if con:
            con.close()