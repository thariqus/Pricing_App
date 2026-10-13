from repository.mysql_connection import get_db_connection
from repository.query import get_latest_version_id_query
from utils.log_error import logger

def get_latest_version_id(db_name="PRICING_DATABASE"):
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