from flask import request, jsonify
from repository.mysql_connection import get_db_connection
from repository.query import create_logger, get_replicated_version
from utils.log_error import logger
import pymysql
import os

PRICE_DB = os.getenv("DB_P_NAME")

def get_replication_version_data(site_code):
    con = None
    cursor = None
    try:
        # Database connection
        con = get_db_connection(PRICE_DB)
        cursor = con.cursor()
        # Execute query

        rep_qry, rep_params = get_replicated_version(site_code)
        cursor.execute(rep_qry, rep_params)

        row = cursor.fetchone()
        version = row[0] if row else 0


        logger_sql_query, logger_params = create_logger(request.remote_addr,"Fetching All Price Data")
        cursor.execute(logger_sql_query, logger_params)
        con.commit()
        return {
            "status": "success",
            "replicated_version" : version
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