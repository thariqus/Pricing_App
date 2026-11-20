import os
import pymysql
from repository.mysql_connection import get_db_connection
from repository.query import filter_discounts
from utils.log_error import logger

DISCOUNT_DB = os.getenv("DB_D_NAME")


def filter_discount_data(data):
    """Run the discount filter for a parsed JSON dict. Returns (body, status)."""
    con = None
    cursor = None
    try:
        sql_query, params = filter_discounts(data)   # raises ValueError on bad input
        logger.info("Filter query built with %s param(s)", len(params))

        con = get_db_connection(DISCOUNT_DB)
        cursor = con.cursor()
        cursor.execute(sql_query, params)
        rows = cursor.fetchall()

        logger.info("Filter completed. Records found: %s", len(rows))
        return {"status": "success", "count": len(rows), "data": rows}, 200

    except ValueError as e:
        logger.warning("Invalid filter request: %s", e)
        return {"status": "error", "message": str(e)}, 400

    except ConnectionError as e:
        logger.error("Database connection error: %s", e)
        return {"status": "error", "message": "Unable to connect to database"}, 503

    except pymysql.MySQLError:
        logger.exception("Database error while filtering discounts")
        return {"status": "error", "message": "Database error"}, 500

    except Exception:
        logger.exception("Unexpected error while filtering discounts")
        return {"status": "error", "message": "Something went wrong"}, 500

    finally:
        if cursor:
            cursor.close()
        if con:
            con.close()