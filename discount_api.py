from flask import jsonify, request
from database.mysql_connection import get_db_connection, DISCOUNT_DB
import logging
import pymysql
from query import (
    select_all_discounts,
    insert_discount_query,
    update_discount,
    check_discount_exists,
    filter_discounts
)
 
 
# Logging configuration
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
 
 
def create_discount():
    logger.info("Entered in create discount")
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
        logger.info("Received discount data")
        # Database connection
        logger.info(f"Connecting to discount DB: {DISCOUNT_DB}")
        con = get_db_connection(DISCOUNT_DB)
        logger.info("Database connection successful")
        cursor = con.cursor()
        # Get insert query
        logger.info("Calling Insert Query")
        sql_query, params = insert_discount_query(data)
        # Execute insert
        cursor.execute(sql_query, params)
        # Save changes
        con.commit()
        # Get newly created ID
        inserted_id = cursor.lastrowid
        logger.info(
            f"Discount inserted successfully. ID: {inserted_id}"
        )
        return jsonify({
            "status": "success",
            "message": "Discount created successfully",
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
        logger.exception("Database error while inserting discount")
        return jsonify({
            "status": "error",
            "message": "Database error",
            "error": str(e)
        }), 500
    except Exception as e:
        if con:
            con.rollback()
        logger.exception(
            "Unexpected error while inserting discount"
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
 
 
def update_discount_data(discount_id):
    logger.info(
        f"Entered in update discount. ID: {discount_id}"
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
        logger.info("Received discount update data")
        # Database connection
        logger.info(f"Connecting to discount DB: {DISCOUNT_DB}")
        con = get_db_connection(DISCOUNT_DB)
        logger.info("Database connection successful")
        cursor = con.cursor()
        # Check whether record exists
        logger.info("Checking whether discount record exists")
        check_query, check_params = check_discount_exists(
            discount_id
        )
        cursor.execute(
            check_query,
            check_params
        )
        existing_discount = cursor.fetchone()
        if not existing_discount:
            return jsonify({
                "status": "error",
                "message": "Discount record not found"
            }), 404
        # Get update query
        logger.info("Calling Update Query")
        sql_query, params = update_discount(
            discount_id,
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
            f"Discount ID {discount_id} updated successfully"
        )
        return jsonify({
            "status": "success",
            "message": "Discount updated successfully",
            "id": discount_id
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
 
 
def filter_discount_data():
    logger.info("Entered in filter discount")
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
        con = get_db_connection(DISCOUNT_DB)
        logger.info("Database connection successful")
        cursor = con.cursor()
        logger.info("Calling Filter Query")
        sql_query, params = filter_discounts(data)
        cursor.execute(sql_query, params)
        discount_data = cursor.fetchall()
        logger.info(
            f"Filter completed. Records found: {len(discount_data)}"
        )
        return jsonify({
            "status": "success",
            "count": len(discount_data),
            "data": discount_data
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
            "Database error while filtering discounts"
        )
        return jsonify({
            "status": "error",
            "message": "Database error"
        }), 500
    except Exception as e:
        logger.exception(
            "Unexpected error while filtering discounts"
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
 