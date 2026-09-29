import os
from flask import jsonify, request
from repository.mysql_connection import get_db_connection
from utils.log_error import logger
from utils.file_path import upload_price_directory
from repository.query import insert_price_query, deactivate_combination_query, create_logger
from data.structure.deactivation_combination import COMBINATION_COLUMNS as combination
import pymysql


PRICE_DB = os.getenv("DB_P_NAME")


def ho_create_price(records, file, invalid_data):
    con = None
    cursor = None
    try:
        con = get_db_connection(PRICE_DB)
        cursor = con.cursor()

        inserted = 0
        deactivated = 0

        for data in records:

            if not isinstance(data, dict) or not data.get("item_no"):
                logger.warning("Skipping record without item_no: %r", data)
                continue

            # 1. old prices for this combination -> inactive
            deact_sql, deact_params = deactivate_combination_query(data,combination=combination)
            cursor.execute(deact_sql, deact_params)
            deactivated += cursor.rowcount

            # 2. new price -> active
            data["active"] = 1
            sql_query, params = insert_price_query(data)
            cursor.execute(sql_query, params)
            inserted += 1

        if file:
            file_path = os.path.join(upload_price_directory, file.filename)
            file.save(file_path)

            logger_sql_query, logger_params = create_logger(
                request.remote_addr, "Insert Item Price CSV Data", file_path
            )
            cursor.execute(logger_sql_query, logger_params)

        con.commit()   # deactivations + inserts land together

        return jsonify({
            "status": "success",
            "message": f"{inserted} price(s) inserted, {deactivated} old price(s) deactivated",
            "count": inserted,
            "deactivated": deactivated,
            "InvalidData": invalid_data
        }), 201

    except ConnectionError as e:
        logger.error(f"Database connection error: {e}")
        return jsonify({
            "status": "error",
            "message": "Unable to connect to database",
            "error": str(e)
        }), 503
    except pymysql.MySQLError as e:
        if con:
            con.rollback()
        logger.exception("Database error while inserting CSV data")
        return jsonify({
            "status": "error",
            "message": "Database error",
            "error": str(e)
        }), 500
    except Exception as e:
        if con:
            con.rollback()
        logger.exception("Unexpected error while inserting CSV data")
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

