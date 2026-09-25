from flask import Flask, jsonify, request, render_template
from repository.mysql_connection import get_db_connection
from repository.query import (
    deactive_exp_price_items, 
    create_logger
    )
import pymysql
from datetime import date
from utils.log_error import logger
from dotenv import load_dotenv
import os
load_dotenv()
PRICE_DB = os.getenv("DB_P_NAME")
VALIDATION_API = os.getenv("VALIDATION_API")


 
def index():
    return render_template("index.html")

def deactive_price_items():
    logger.info("Entered in deactive_items function")
    con = None
    cursor = None
    try:
        logger.info("Connecting to database")
        con = get_db_connection(PRICE_DB)
        logger.info("Database connection successful")
        cursor = con.cursor()
        logger.info("Calling Update Query")
        today = date.today()
        sql_query = deactive_exp_price_items()
        logger.info("Executing update query")
        cursor.execute(sql_query, today)
        updated_rows = cursor.rowcount
        logger_sql_query, logger_params = create_logger(request.remote_addr,f"{updated_rows} items price expired")
        cursor.execute(logger_sql_query, logger_params)
        con.commit()
        logger.info(
            f"Updated successfully. Rows affected: {updated_rows}"
        )
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

