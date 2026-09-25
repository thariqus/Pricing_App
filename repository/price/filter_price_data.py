from flask import jsonify
from repository.query import filter_prices
from repository.mysql_connection import get_db_connection
import os
from utils.log_error import logger
import pymysql
PRICE_DB = os.getenv("DB_P_NAME")

def filter_price_data(data):
    con = None
    cursor = None
    try:
        if data is None:
            return jsonify({
                "status": "error",
                "message": "Request must contain valid JSON"
            }), 400
        page  = int(data.get("page") or 1)
        limit = int(data.get("limit") or 500)
 
        if page < 1 or limit < 1 or limit > 500:
            return jsonify({
                "status": "error",
                "message": "Invalid page or limit"
            }), 400
        con = get_db_connection(PRICE_DB)
        cursor = con.cursor()
        sql_query, count_query, params, count_params = filter_prices(
            data, page, limit
        )
        cursor.execute(sql_query, params)
        price_data = cursor.fetchall()
        cursor.execute(count_query, count_params)
        total = cursor.fetchone()["total"]
        for row in price_data:
            for field in ("starting_date", "ending_date"):
                value = row.get(field)
                if value is not None:
                    row[field] = value.strftime("%Y-%m-%d %H:%M:%S")
        return jsonify({
            "status": "success",
            "page": page,
            "limit": limit,
            "total": total,
            "data": price_data
        }), 200
    except ConnectionError as e:
        logger.error(
            f"Database connection error: {e}"
        )
        return jsonify({
            "status": "error",
            "message": "Unable to connect to database"
        }), 503
    except pymysql.MySQLError as e:
        logger.exception(
            "Database error while filtering prices"
        )
        return jsonify({
            "status": "error",
            "message": "Database error"
        }), 500
    except Exception as e:
        logger.exception(
            "Unexpected error while filtering prices"
        )
        return jsonify({
            "status": "error",
            "message": "Something went wrong"
        }), 500
    finally:
        if cursor:
            cursor.close()
        if con:
            con.close()