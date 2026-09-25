import os
from flask import jsonify, request
import requests
from repository.mysql_connection import get_db_connection
from utils.log_error import logger
from utils.date_converter import convert_datetime
from utils.file_path import upload_price_directory
from repository.query import insert_price_query, create_logger
import pymysql


PRICE_DB = os.getenv("DB_P_NAME")
VALIDATION_API = os.getenv("VALIDATION_API")

def create_price(records, file, invalid_data):
    con = None
    cursor = None
    try:
        con = get_db_connection(PRICE_DB)
        cursor = con.cursor()
        for data in records:
            sql_query, params = insert_price_query(data)
            cursor.execute(sql_query, params)
        file_path = os.path.join(
            upload_price_directory,
            file.filename
        )
        file.save(file_path)
        logger_sql_query, logger_params = create_logger(request.remote_addr,"Insert Item Price CSV Data",file_path)
        cursor.execute(logger_sql_query, logger_params)
        con.commit()
        return jsonify({
            "status": "success",
            "message": "CSV data inserted successfully",
            "count": len(records),
            "InvalidData": invalid_data
        }), 201
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
            "Database error while inserting CSV data"
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
            "Unexpected error while inserting CSV data"
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