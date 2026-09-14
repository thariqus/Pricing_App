from flask import Flask, jsonify, request
from database import get_db_connection
from query import select_all_prices, insert_price_query, update_price, check_price_exists, filter_prices
import logging
import pymysql

app = Flask(__name__)


# Logging configuration
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)


def fetch_all_prices():
    logger.info("Entered in fetch all prices")
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
        logger.info("Connecting to database")
        con = get_db_connection()
        logger.info("Database connection successful")
        cursor = con.cursor()
        # Execute query
        logger.info("Calling Select Query")
        sel_query, params = select_all_prices(page, limit)
        cursor.execute(sel_query, params)
        price_data = cursor.fetchall()
        logger.info("Returning Data")
        return jsonify({
            "status": "success",
            "page": page,
            "limit": limit,
            "data": price_data
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

def create_price():
    logger.info("Entered in create price")
    con = None
    cursor = None
    try:
        # Get JSON data
        data = request.get_json()
        if not data:
            return jsonify({
                "status": "error",
                "message": "Request body is empty"
            }), 400
        logger.info("Received pricing data")
        # Database connection
        logger.info("Connecting to database")
        con = get_db_connection()
        logger.info("Database connection successful")
        cursor = con.cursor()
        # Get insert query
        logger.info("Calling Insert Query")
        sql_query, params = insert_price_query(data)
        # Execute insert
        cursor.execute(sql_query, params)
        # Save changes
        con.commit()
        # Get newly created ID
        inserted_id = cursor.lastrowid
        logger.info(
            f"Price inserted successfully. ID: {inserted_id}"
        )
        return jsonify({
            "status": "success",
            "message": "Price created successfully",
            "id": inserted_id
        }), 201
    except ConnectionError as e:
        logger.error(f"Database connection error: {e}")
        return jsonify({
            "status": "error",
            "message": "Unable to connect to database",
            "error": str(e)
        }), 503
    except pymysql.MySQLError as e:
        if con:
            con.rollback()
        logger.exception("Database error while inserting price")
        return jsonify({
            "status": "error",
            "message": "Database error",
            "error": str(e)
        }), 500
    except Exception as e:
        if con:
            con.rollback()
        logger.exception(
            "Unexpected error while inserting price"
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

def update_price_data(price_id):
    logger.info(
        f"Entered in update price. ID: {price_id}"
    )
    con = None
    cursor = None
    try:
        # Get JSON data
        data = request.get_json()
        if not data:
            return jsonify({
                "status": "error",
                "message": "Request body is empty"
            }), 400
        logger.info("Received pricing update data")
        # Database connection
        logger.info("Connecting to database")
        con = get_db_connection()
        logger.info("Database connection successful")
        cursor = con.cursor()
        # Check whether record exists
        logger.info("Checking whether price record exists")
        check_query, check_params = check_price_exists(
            price_id
        )
        cursor.execute(
            check_query,
            check_params
        )
        existing_price = cursor.fetchone()
        if not existing_price:
            return jsonify({
                "status": "error",
                "message": "Price record not found"
            }), 404
        # Get update query
        logger.info("Calling Update Query")
        sql_query, params = update_price(
            price_id,
            data
        )
        # Execute update
        cursor.execute(
            sql_query,
            params
        )
        # Save changes
        con.commit()
        logger.info(
            f"Price ID {price_id} updated successfully"
        )
        return jsonify({
            "status": "success",
            "message": "Price updated successfully",
            "id": price_id
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

def filter_price_data():
    logger.info("Entered in filter price")
    con = None
    cursor = None
    try:
        data = request.get_json(silent=True)
        if data is None:
            return jsonify({
                "status": "error",
                "message": "Request must contain valid JSON"
            }), 400
        logger.info("Received filter data")
        con = get_db_connection()
        logger.info("Database connection successful")
        cursor = con.cursor()
        logger.info("Calling Filter Query")
        sql_query, params = filter_prices(data)
        cursor.execute(sql_query, params)
        price_data = cursor.fetchall()
        logger.info(
            f"Filter completed. Records found: {len(price_data)}"
        )
        return jsonify({
            "status": "success",
            "count": len(price_data),
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