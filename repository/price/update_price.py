from flask import request, jsonify
from repository.mysql_connection import get_db_connection
from utils.log_error import logger
import os
from repository.query import check_price_exists, update_price, create_logger
import pymysql

PRICE_DB = os.getenv("DB_P_NAME")


def update_price_data(data):
    con = None
    cursor = None
    try:
        con = get_db_connection(PRICE_DB)
        cursor = con.cursor()
        updated_records = []
        failed_records = []
        for record in data:
            price_id = record.get("id")
            if not price_id:
                failed_records.append({
                    "data": record,
                    "message": "Price ID is required"
                })
                continue
            check_query, check_params = check_price_exists(price_id)
            cursor.execute(
                check_query,
                check_params
            )
            existing_price = cursor.fetchone()
            if not existing_price:
                failed_records.append({
                    "id": price_id,
                    "message": "Price record not found"
                })
                continue
            update_data = {
                key: value
                for key, value in record.items()
                if key != "id"
            }
            if not update_data:
                failed_records.append({
                    "id": price_id,
                    "message": "No fields to update"
                })
                continue
            sql_query, params = update_price(
                price_id,
                update_data
            )
            cursor.execute(
                sql_query,
                params
            )
            logger_sql_query, logger_params = create_logger(
                request.remote_addr,
                f"Item price number {price_id} Update"
            )
            cursor.execute(
                logger_sql_query,
                logger_params
            )
            updated_records.append({
                "id": price_id
            })
        con.commit()
        return jsonify({
            "status": "success",
            "message": "Price update completed",
            "updated_count": len(updated_records),
            "updated": updated_records,
            "failed_count": len(failed_records),
            "failed": failed_records
        }), 200
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
            "Database error while updating price"
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
            "Unexpected error while updating price"
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
