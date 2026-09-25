from flask import request, jsonify
from repository.mysql_connection import get_db_connection
from utils.log_error import logger
import os
from repository.query import select_all_prices, create_logger, filter_prices, get_item_price_details
import pymysql

PRICE_DB = os.getenv("DB_P_NAME")


def fetch_all_prices():
    logger.info("Entered in fetch all prices")
    con = None
    cursor = None
    try:
        # Get pagination values
        page = request.args.get("page", default=1, type=int)
        limit = request.args.get("limit", default=100, type=int)
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
        con = get_db_connection(PRICE_DB)
        logger.info("Database connection successful")
        cursor = con.cursor()
        # Execute query
        logger.info("Calling Select Query")
        sel_query, count_query, params = select_all_prices(page, limit)
        cursor.execute(sel_query, params)
        price_data = cursor.fetchall()
        cursor.execute(count_query)
        total_records = cursor.fetchone()["total"]
        logger.info("Returning Data")
        logger_sql_query, logger_params = create_logger(request.remote_addr,"Fetching All Price Data")
        cursor.execute(logger_sql_query, logger_params)
        con.commit()
        return jsonify({
            "status": "success",
            "page": page,
            "limit": limit,
            "data": price_data,
            "total": total_records,
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
        con = get_db_connection(PRICE_DB)
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

def get_prices():
    logger.info("Enter into get price function")
    con = None
    cursor = None
    try:
        data = request.get_json()
        logger.info("Connecting to database")
        con = get_db_connection(PRICE_DB)
        logger.info("Database connection successful")
        cursor = con.cursor()
        if not data:
            return jsonify({
                "status": "error",
                "message": "Request data is empty"
            }), 400
        customer_no = bool(data["Customer_No"])
        customer_group = bool(data["Customer_Group"])
        customer_hierarchy = bool(data["Customer_Hierarchy"])
        distribution_channel_code = bool(data["Distribution_Channel_Code"])
        location_code = bool(data["Location_Code"])
        sales_organization_code = bool(data["Sales_Organization_Code"])
        uom = bool(data["uom"])
        transportation_zone_code = bool(data["Transportation_Zone_Code"])
        sql_query = get_item_price_details()
        if sales_organization_code and distribution_channel_code and customer_no and location_code and uom:
            cursor.execute(sql_query, 1)
        elif sales_organization_code and distribution_channel_code and customer_group and location_code and uom:
            cursor.execute(sql_query, 2)
        elif sales_organization_code and distribution_channel_code and customer_no and uom:
            cursor.execute(sql_query, 3)
        elif sales_organization_code and distribution_channel_code and customer_group and uom:
            cursor.execute(sql_query, 4)
        elif sales_organization_code and customer_group and uom:
            cursor.execute(sql_query, 5)
        elif sales_organization_code and customer_hierarchy and location_code and uom:
            cursor.execute(sql_query, 6)
        elif sales_organization_code and customer_hierarchy and uom:
            cursor.execute(sql_query, 7)
        elif sales_organization_code and distribution_channel_code and location_code and transportation_zone_code and uom:
            cursor.execute(sql_query, 8)
        elif sales_organization_code and distribution_channel_code and location_code and uom:
            cursor.execute(sql_query, 9)
        elif sales_organization_code and distribution_channel_code and uom:
            cursor.execute(sql_query, 10)
        elif sales_organization_code and uom:
            cursor.execute(sql_query, 11)
        else:
            cursor.execute(sql_query, 0)
        items_datas = cursor.fetchall()
        logger_sql_query, logger_params = create_logger(request.remote_addr,"Fetching item pricing prioritys")
        cursor.execute(logger_sql_query, logger_params)
        con.commit()
        return {
            "status" : "Success",
            "data" : items_datas
            }
    except ConnectionError:
        if con:
            con.rollback()
        logger.exception(
            "Database connection error"
        )
        raise
    except pymysql.MySQLError:
        if con:
            con.rollback()
        logger.exception(
            "Database error while updating price"
        )
        raise
    except Exception:
        if con:
            con.rollback()
        logger.exception(
            "Unexpected error while updating price"
        )
        raise
    finally:
        if cursor:
            cursor.close()
        if con:
            con.close()
