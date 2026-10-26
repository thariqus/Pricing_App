import os
from repository.mysql_connection import get_db_connection
from repository.query import insert_log_message_query
from utils.log_error import logger


def write_log(custom_message, ipaddress, response_message, source, log_type,
              message_code, log_status, info=False, error=False, site_details=None):
    """Save one row to log_message. Never raises."""
    con = None
    try:
        entry = {
            "custom_message":   str(custom_message or "")[:500],
            "response_message": str(response_message or "")[:500],
            "source":           str(source or "")[:20],
            "type":             str(log_type or "")[:20],
            "site_details":     str(site_details or os.getenv("STORE_SITE_CODE", ""))[:100],
            "message_code":     str(message_code or "")[:5],
            "log_status":       int(log_status or 0),
            "info":             1 if info else 0,
            "error":            1 if error else 0,
            "ipaddress":        str(ipaddress or ""),
        }

        con = get_db_connection(os.getenv("DB_P_NAME"))
        with con.cursor() as cursor:
            cursor.execute(*insert_log_message_query(entry))
        con.commit()

    except Exception:
        logger.exception("Failed to write log message")

    finally:
        if con:
            con.close()