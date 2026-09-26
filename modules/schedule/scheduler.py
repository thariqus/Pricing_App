from flask import request
from repository.mysql_connection import get_db_connection
from utils.log_error import logger
from datetime import date, datetime
from repository.query import deactive_exp_price_items, create_logger, active_valid_price_items, check_pending_active_items
from utils.date_converter import converter
import os
import pymysql
PRICE_DB = os.getenv("DB_P_NAME")

def deactive_price_items():
    con = None
    cursor = None
    try:
        con = get_db_connection(PRICE_DB)
        cursor = con.cursor()
        today = datetime.now()
        sql_query = deactive_exp_price_items()
        cursor.execute(sql_query, (today,))
        updated_rows = cursor.rowcount
        logger_sql_query, logger_params = create_logger('',f"{updated_rows} Invalid item deactivated.")
        cursor.execute(logger_sql_query, logger_params)
        con.commit()
        return {
            "status": "success",
            "message": "Items updated successfully",
            "updated_rows": updated_rows
        }
    except ConnectionError:
        if con:
            con.rollback()
        logger.exception(
            "Database connection error"
        )
        raise
    except pymysql.MySQLError:
        if con:
            con.rollback()
        logger.exception(
            "Database error while updating price"
        )
        raise
    except Exception:
        if con:
            con.rollback()
        logger.exception(
            "Unexpected error while updating price"
        )
        raise
    finally:
        if cursor:
            cursor.close()
        if con:
            con.close()

def active_price_items():
    con = None
    cursor = None
    try:
        con = get_db_connection(PRICE_DB)
        cursor = con.cursor()

        today = datetime.now()
        con_date = converter(today)
        pending_check = check_pending_active_items()
        cursor.execute(pending_check, (con_date,con_date))
        data = cursor.fetchone()
        print(data)


        today = datetime.now()
        convert_date = converter(today)
        sql_query = active_valid_price_items()
        cursor.execute(sql_query, (convert_date,))
        updated_rows = cursor.rowcount
        logger_sql_query, logger_params = create_logger('',f"{updated_rows} Valid items activated.")
        cursor.execute(logger_sql_query, logger_params)
        con.commit()
        return {
            "status": "success",
            "message": "Activation updated successfully",
            "updated_rows": updated_rows
        }
    except ConnectionError:
        if con:
            con.rollback()
        logger.exception(
            "Database connection error"
        )
        raise
    except pymysql.MySQLError:
        if con:
            con.rollback()
        logger.exception(
            "Database error while updating price"
        )
        raise
    except Exception:
        if con:
            con.rollback()
        logger.exception(
            "Unexpected error while updating price"
        )
        raise
    finally:
        if cursor:
            cursor.close()
        if con:
            con.close()