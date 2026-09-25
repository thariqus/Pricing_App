from flask import jsonify, request
from repository.query import get_item_price_details, create_logger
from repository.mysql_connection import get_db_connection
from utils.log_error import logger
import pymysql
import os
PRICE_DB = os.getenv("DB_P_NAME")

def get_price_priority(data):
    con = None
    cursor = None
    try:
        con = get_db_connection(PRICE_DB)
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
