from flask import jsonify
from utils.log_error import logger
import pymysql
from repository.mysql_connection import get_db_connection
import os
from repository.query import update_site_qry

PRICE_DB = os.getenv("DB_P_NAME")


def edit_one_site(site_id, data):
    con = None
    cursor = None

    try:
        # Database connection
        con = get_db_connection(PRICE_DB)
        cursor = con.cursor()

        # Get query and parameters
        update_query, params = update_site_qry(site_id, data)

        # Execute query
        cursor.execute(update_query, params)

        # Check whether the site exists
        if cursor.rowcount == 0:
            con.rollback()

            return jsonify({
                "status": "error",
                "message": "Site not found or no changes made"
            }), 404

        # Commit changes
        con.commit()

        return jsonify({
            "status": "success",
            "message": "Site updated successfully"
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

        logger.exception("Database error while updating site")

        return jsonify({
            "status": "error",
            "message": "Database error"
        }), 500

    except Exception as e:
        if con:
            con.rollback()

        logger.exception("Unexpected error while updating site")

        return jsonify({
            "status": "error",
            "message": "Something went wrong"
        }), 500

    finally:
        if cursor:
            cursor.close()

        if con:
            con.close()
