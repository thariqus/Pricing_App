from flask import jsonify
from repository.mysql_connection import get_db_connection
import os
from utils.log_error import logger
import pymysql
from repository.query import insert_site_settings

PRICE_DB = os.getenv("DB_P_NAME")

def add_site_details(data):
    con = None
    cursor = None
    try:
        if not data:
            return jsonify({
                "status" : "error",
                "message" : "give data is empty"
            })
        # Database connection
        con = get_db_connection(PRICE_DB)
        cursor = con.cursor()
        # Execute query

        for sites in data['sites']:
            sql_query, params = insert_site_settings(sites)
            cursor.execute(sql_query, params)
        con.commit()

        return {
            "status" : "Success",
            "message": "site settings created successfully"
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