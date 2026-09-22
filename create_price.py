import os
from flask import jsonify, request
import requests
from database.mysql_connection import get_db_connection
from utils.log_error import logger
from utils.date_converter import convert_datetime
from utils.file_path import upload_price_directory
from database.query import insert_price_query, create_logger
import pymysql


PRICE_DB = os.getenv("DB_P_NAME")
VALIDATION_API = os.getenv("VALIDATION_API")


def create_price(records, file):
    logger.info("Entered in create price")
    con = None
    cursor = None
    Invalid_item_data = []
    try:
        if not records:
            return jsonify({
                "status": "error",
                "message": "CSV file contains no records"
            }), 400
        logger.info(
            f"Received {len(records)} pricing records"
        )
        logger.info("Connecting to database")
        con = get_db_connection(PRICE_DB)
        logger.info("Database connection successful")
        cursor = con.cursor()
        validation_records = [
            {
                "item_code": data.get("item_no"),
                "uom": data.get("uom")
            }
            for data in records
        ]
        response = requests.post(
            VALIDATION_API,
            json=validation_records,
            timeout=60
        )
        response_message = response.json()
        items_no = response_message["message"]["item"]["item_codes"]
        uoms = response_message["message"]["item_uoms"]["item_uom"]
        for data in records:
            if data["item_no"] in items_no:
               data["reason"] = "Item Not Found"
               Invalid_item_data.append(data)
            else:
                if data["uom"] in uoms:
                    data["reason"] = "UOM Not Found"
                    Invalid_item_data.append(data)
                else:
                    logger.info("Calling Insert Query")
                    data["starting_date"] = convert_datetime(
                        data.get("starting_date")
                    )

                    data["ending_date"] = convert_datetime(
                        data.get("ending_date")
                    )
                    print(data["starting_date"])
                    sql_query, params = insert_price_query(data)
                    cursor.execute(sql_query, params)
        file_path = os.path.join(
            upload_price_directory,
            file.filename
        )
        file.save(file_path)
        logger_sql_query, logger_params = create_logger(request.remote_addr,"Insert Item Price CSV Data",file_path)
        cursor.execute(logger_sql_query, logger_params)
        con.commit()
        logger.info(
            f"{len(records)} price records inserted successfully"
        )
        return jsonify({
            "status": "success",
            "message": "CSV data inserted successfully",
            "count": len(records),
            "InvalidData": Invalid_item_data
        }), 201
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
            "Database error while inserting CSV data"
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
            "Unexpected error while inserting CSV data"
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