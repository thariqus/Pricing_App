from flask import jsonify
import pymysql
from repository.mysql_connection import get_db_connection
import os
from utils.log_error import logger
from repository.query import select_all_sites
PRICE_DB = os.getenv("DB_P_NAME")

def get_all_site_data():
    con = None
    cursor = None
    try:
        # Database connection
        con = get_db_connection(PRICE_DB)
        cursor = con.cursor()
        # Execute query
        sel_query = select_all_sites()
        cursor.execute(sel_query)
        site_datas = cursor.fetchall()
        return jsonify({
            "status": "success",
            "data": site_datas
        })
    except ConnectionError as e:
        logger.error(f"Database connection error: {e}")
        return jsonify({
            "status": "error",
            "message": "Unable to connect to database",
            "error": str(e)
        }), 503
    except pymysql.MySQLError as e:
        logger.exception("Database error while fetching prices")
        return jsonify({
            "status": "error",
            "message": "Database error",
            "error": str(e)
        }), 500
    except Exception as e:
        logger.exception(
            "Unexpected error while fetching prices data"
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