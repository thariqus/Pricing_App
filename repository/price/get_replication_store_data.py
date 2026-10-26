from flask import request, jsonify
from repository.mysql_connection import get_db_connection
from repository.query import get_data_replication
from utils.log_error import logger
import pymysql
import os

PRICE_DB = os.getenv("DB_P_NAME")

def get_replication_store_data(version_id):
    con = None
    cursor = None
    try:
        # Database connection
        con = get_db_connection(PRICE_DB)
        cursor = con.cursor()
        # Execute query
        sel_query, params = get_data_replication(version_id, "2113") #get the site code automatically
        cursor.execute(sel_query, params)
        replication_data = cursor.fetchall()

        return {
            "status": "success",
            "data" : replication_data
        }
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