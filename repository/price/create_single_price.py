from flask import request, jsonify
import pymysql
from repository.mysql_connection import get_db_connection
from utils.log_error import logger
from repository.query import insert_price_query, create_logger
import os

PRICE_DB = os.getenv("DB_P_NAME")


def create_single_price(data):
    con = None
    cursor = None
    try:
        if not data:
            return jsonify({
                "status": "error",
                "message": "Request data is empty"
            }), 400
        con = get_db_connection(PRICE_DB)
        cursor = con.cursor()
        sql_query, params = insert_price_query(data)
        cursor.execute(
            sql_query,
            params
        )
        inserted_id = cursor.lastrowid
        con.commit()
        logger_sql_query, logger_params = create_logger(request.remote_addr,"Insert Single Item Price Data")
        cursor.execute(logger_sql_query, logger_params)
        con.commit()
        return {
            "status": "success",
            "message": "Price created successfully",
            "id": inserted_id
        }
    except ConnectionError as e:
        logger.error(
            f"Database connection error: {e}"
        )
        return jsonify({
            "status": "error",
            "message": "Unable to connect to database",
            "error": str(e)
        }), 503
    except pymysql.MySQLError as e:
        if con:
            con.rollback()
        logger.exception(
            "Database error while creating price"
        )
        return jsonify({
            "status": "error",
            "message": "Database error",
            "error": str(e)
        }), 500
    except Exception as e:
        if con:
            con.rollback()
        logger.exception(
            "Unexpected error while creating price"
        )
        return jsonify({
            "status": "error",
            "message": "Something went wrong",
            "error": str(e)
        }), 500
    finally:
        if cursor:
            cursor.close()
        if con:
            con.close()