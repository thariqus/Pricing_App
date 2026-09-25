from flask import jsonify, request
from repository.mysql_connection import get_db_connection, DISCOUNT_DB
import logging
import pymysql
from repository.query import (
    select_all_discounts
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
 
logger = logging.getLogger(__name__)
 

def fetch_all_discounts():
    logger.info("Entered in fetch all discounts")
    con = None
    cursor = None
    try:
        # Get pagination values
        page = request.args.get("page", default=1, type=int)
        limit = request.args.get("limit", default=10, type=int)
        # Validate pagination
        if page < 1:
            return jsonify({
                "status": "error",
                "message": "Page must be greater than 0"
            }), 400
        if limit < 1 or limit > 100:
            return jsonify({
                "status": "error",
                "message": "Limit must be between 1 and 100"
            }), 400
        logger.info(
            f"Pagination - page: {page}, limit: {limit}"
        )
        # Database connection
        logger.info(f"Connecting to discount DB: {DISCOUNT_DB}")
        con = get_db_connection(DISCOUNT_DB)
        logger.info("Database connection successful")
        cursor = con.cursor()
        # Execute query
        logger.info("Calling Select Discount Query")
        sel_query, params = select_all_discounts(page, limit)
        cursor.execute(sel_query, params)
        discount_data = cursor.fetchall()
        logger.info("Returning Data")
        return jsonify({
            "status": "success",
            "page": page,
            "limit": limit,
            "data": discount_data
        })
    except ConnectionError as e:
        logger.error(f"Database connection error: {e}")
        return jsonify({
            "status": "error",
            "message": "Unable to connect to database",
            "error": str(e)
        }), 503
    except pymysql.MySQLError as e:
        logger.exception("Database error while fetching discounts")
        return jsonify({
            "status": "error",
            "message": "Database error",
            "error": str(e)
        }), 500
    except Exception as e:
        logger.exception(
            "Unexpected error while fetching discounts data"
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
 