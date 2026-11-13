from flask import request, jsonify
from repository.mysql_connection import get_db_connection
from utils.log_error import logger
import os
from repository.query import check_discount_exists, update_discount
import pymysql

DISCOUNT_DB = os.getenv("DB_D_NAME")


def update_discount_data(data):
    con = None
    cursor = None
    try:
        con = get_db_connection(DISCOUNT_DB)
        cursor = con.cursor()
        updated_records = []
        failed_records = []
        for record in data:
            discount_id = record.get("id")
            if not discount_id:
                failed_records.append({
                    "data": record,
                    "message": "Discount ID is required"
                })
                continue
            check_query, check_params = check_discount_exists(discount_id)
            cursor.execute(
                check_query,
                check_params
            )
            existing_discount = cursor.fetchone()
            if not existing_discount:
                failed_records.append({
                    "id": discount_id,
                    "message": "Discount record not found"
                })
                continue
            update_data = {
                key: value
                for key, value in record.items()
                if key != "id"
            }
            if not update_data:
                failed_records.append({
                    "id": discount_id,
                    "message": "No fields to update"
                })
                continue
            sql_query, params = update_discount(
                discount_id,
                update_data
            )
            cursor.execute(
                sql_query,
                params
            )
            updated_records.append({
                "id": discount_id
            })
        con.commit()
        return jsonify({
            "status": "success",
            "message": "Discount update completed",
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
            "Database error while updating discount"
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
            "Unexpected error while updating discount"
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