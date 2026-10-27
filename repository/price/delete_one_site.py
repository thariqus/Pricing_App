from flask import jsonify
from utils.log_error import logger
import pymysql
from repository.mysql_connection import get_db_connection
import os
from repository.query import delete_site_qry

PRICE_DB = os.getenv("DB_P_NAME")


def delete_one_site(site_id):
    con = None
    cursor = None

    try:
        # Database connection
        con = get_db_connection(PRICE_DB)
        cursor = con.cursor()

        # Get query and parameters
        sel_query, params = delete_site_qry(site_id)

        # Execute query
        cursor.execute(sel_query, params)

        # Check whether a row was deleted
        if cursor.rowcount == 0:
            return jsonify({
                "status": "error",
                "message": "Site not found"
            }), 404

        # Commit changes
        con.commit()

        return jsonify({
            "status": "success",
            "message": "Deleted successfully"
        }), 200

    except ConnectionError as e:
        logger.error(f"Database connection error: {e}")

        return jsonify({
            "status": "error",
            "message": "Unable to connect to database"
        }), 503

    except pymysql.MySQLError as e:
        if con:
            con.rollback()

        logger.exception("Database error while deleting site")

        return jsonify({
            "status": "error",
            "message": "Database error"
        }), 500

    except Exception as e:
        if con:
            con.rollback()

        logger.exception("Unexpected error while deleting site")

        return jsonify({
            "status": "error",
            "message": "Something went wrong"
        }), 500

    finally:
        if cursor:
            cursor.close()

        if con:
            con.close()
