from flask import jsonify, request
from repository.mysql_connection import get_db_connection
import pymysql
from repository.query import (
    select_all_discounts,
    insert_discount_query,
    update_discount,
    check_discount_exists,
    filter_discounts,
    deactive_exp_discount_items,
    get_item_discount_details
)
from utils.discount_validation import validate_discount_rows
from utils.date_converter import convert_datetime, converter
from datetime import date
from utils.log_error import logger
from dotenv import load_dotenv
import os
load_dotenv()
DISCOUNT_DB = os.getenv("DB_D_NAME")
 
def fetch_all_discounts():
    logger.info("Entered in fetch all discounts")
    con = None
    cursor = None
    try:
        # Get pagination values
        page = request.args.get("page", default=1, type=int)
        limit = request.args.get("limit", default=100, type=int)

        # Active filter: sent in the JSON body (or as ?active= in the URL)
        body = request.get_json(silent=True) or {}
        active = body.get("active", request.args.get("active"))

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
            f"Pagination - page: {page}, limit: {limit}, active: {active}"
        )

        # Database connection
        logger.info(f"Connecting to discount DB: {DISCOUNT_DB}")
        con = get_db_connection(DISCOUNT_DB)
        logger.info("Database connection successful")
        cursor = con.cursor()

        # Execute query with the active filter applied
        logger.info("Calling Select Discount Query")
        sel_query, params = select_all_discounts(page, limit, active)
        cursor.execute(sel_query, params)
        discount_data = cursor.fetchall()
        logger.info(f"Returning {len(discount_data)} rows")

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


from utils.discount_validation import validate_discount_rows


def create_discount(records, file):
    logger.info("Entered in create discount")
    con = None
    cursor = None
    try:
        if not records:
            return jsonify({
                "status": "error",
                "message": "CSV file contains no records"
            }), 400

        valid, invalid = validate_discount_rows(records)
        if invalid:
            logger.warning(f"Discount CSV rejected: {len(invalid)} invalid row(s)")
            return jsonify({
                "status": "error",
                "message": (f"{len(invalid)} row(s) failed validation. "
                            "Nothing was imported. Fix these rows and upload again."),
                "count": 0,
                "invalid_data": invalid
            }), 400

        con = get_db_connection(DISCOUNT_DB)
        cursor = con.cursor()

        for data in valid:
            sql_query, params = insert_discount_query(data)
            cursor.execute(sql_query, params)

        con.commit()
        logger.info(f"Discount CSV imported: {len(valid)} row(s)")

        return jsonify({
            "status": "success",
            "message": f"{len(valid)} discount(s) created successfully",
            "count": len(valid),
            "invalid_data": []
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
        logger.exception("Database error while inserting discount CSV")
        return jsonify({
            "status": "error",
            "message": "Database error. Nothing was imported.",
            "error": str(e)
        }), 500
    except Exception as e:
        if con:
            con.rollback()
        logger.exception("Unexpected error while inserting discount CSV")
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


def update_discount(discount_id, data):
    fields = {k: v for k, v in data.items() if k in DISCOUNT_UPDATABLE}
    if not fields:
        raise ValueError("No valid fields provided for update")
    set_clause = ", ".join(f"{k} = %s" for k in fields)
    sql_query = f"UPDATE DISCOUNT_TABLE SET {set_clause} WHERE id = %s"
    params = tuple(list(fields.values()) + [discount_id])
    return sql_query, params

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
from datetime import datetime

DISCOUNT_TABLE = "discounts"  # change to your actual table name

# UI filter key -> actual DB column. Only these columns can be filtered.
FILTER_COLUMNS = {
    "condition_type": "condition_type",
    "item_no": "item_no",
    "customer": "customer",
    "customer_group": "customer_group",
    "customer_hierarchy": "customer_hierarchy",
    "sales_org": "sales_organization",
    "distribution_channel": "distribution_channel",
    "location_code": "location_code",
    "sales_price": "sales_price",
    "currency": "currency",
    "unit_of_measure": "unit_of_measure",
    "minimum_quantity": "minimum_quantity",
    "lower_limit": "lower_limit",
    "upper_limit": "upper_limit",
    "transportation_zone": "transportation_zone",
    "zone_code": "zone_code",
    "priority": "priority",
    "offer_article": "offer_article",
}

# Columns that use range logic instead of exact match
DATE_FROM_COLUMNS = {"starting_date": "starting_date"}   # starting_date >= value
DATE_TO_COLUMNS = {"ending_date": "ending_date"}         # ending_date <= value

# Sort By options -> actual DB column
SORT_COLUMNS = {
    "item_no": "item_no",
    "sales_price": "sales_price",
    "starting_date": "starting_date",
    "ending_date": "ending_date",
    "priority": "priority",
    "lower_limit": "lower_limit",
    "upper_limit": "upper_limit",
}


def _parse_date(value):
    try:
        return datetime.strptime(str(value), "%Y-%m-%d").date()
    except ValueError:
        raise ValueError(f"Invalid date '{value}', expected YYYY-MM-DD")


def build_discount_filter_query(data):
    """
    Expects JSON like:
    {
        "filters": {
            "active": "All" | "Active" | "Inactive",
            "item_no": "1000047",
            "sales_price": "12",
            "starting_date": "2026-10-01",
            "ending_date": "2026-12-31",
            ...
        },
        "sort_by": "item_no",
        "sort_order": "asc" | "desc"
    }
    """
    filters = data.get("filters") or {}
    if not isinstance(filters, dict):
        raise ValueError("'filters' must be an object")

    where_clauses = []
    params = []

    for key, raw_value in filters.items():
        if raw_value is None or (isinstance(raw_value, str) and raw_value.strip() == ""):
            continue

        value = raw_value.strip() if isinstance(raw_value, str) else raw_value

        # Active / status dropdown
        if key == "active":
            if str(value).lower() == "all":
                continue
            where_clauses.append("active = %s")
            params.append(1 if str(value).lower() == "active" else 0)
            continue

        if key in DATE_FROM_COLUMNS:
            where_clauses.append(f"{DATE_FROM_COLUMNS[key]} >= %s")
            params.append(_parse_date(value))
            continue

        if key in DATE_TO_COLUMNS:
            where_clauses.append(f"{DATE_TO_COLUMNS[key]} <= %s")
            params.append(_parse_date(value))
            continue

        if key not in FILTER_COLUMNS:
            raise ValueError(f"Unsupported filter: {key}")

        column = FILTER_COLUMNS[key]
        where_clauses.append(f"{column} = %s")
        params.append(value)

    sql = f"SELECT * FROM {DISCOUNT_TABLE}"
    if where_clauses:
        sql += " WHERE " + " AND ".join(where_clauses)

    # Sorting (whitelisted, so it is safe to put in the query string)
    sort_by = SORT_COLUMNS.get(data.get("sort_by"))
    if sort_by:
        sort_order = "DESC" if str(data.get("sort_order", "asc")).lower() == "desc" else "ASC"
        sql += f" ORDER BY {sort_by} {sort_order}"

    return sql, params

def filter_discount_data():
    logger.info("Entered in filter discount")
    con = None
    cursor = None
    try:
        data = request.get_json(silent=True)
        if data is None or not isinstance(data, dict):
            return jsonify({
                "status": "error",
                "message": "Request must contain valid JSON object"
            }), 400

        logger.info(f"Received filter data: {data}")

        con = get_db_connection(DISCOUNT_DB)
        logger.info("Database connection successful")
        cursor = con.cursor()

        sql_query, params = filter_discounts(data)
        logger.info(f"Built query: {sql_query} | params: {params}")

        cursor.execute(sql_query, params)
        discount_data = cursor.fetchall()

        logger.info(f"Filter completed. Records found: {len(discount_data)}")
        return jsonify({
            "status": "success",
            "count": len(discount_data),
            "data": discount_data
        }), 200

    except ValueError as e:
        logger.warning(f"Invalid filter request: {e}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 400
    except ConnectionError as e:
        logger.error(f"Database connection error: {e}")
        return jsonify({
            "status": "error",
            "message": "Unable to connect to database"
        }), 503
    except pymysql.MySQLError:
        logger.exception("Database error while filtering discounts")
        return jsonify({
            "status": "error",
            "message": "Database error"
        }), 500
    except Exception:
        logger.exception("Unexpected error while filtering discounts")
        return jsonify({
            "status": "error",
            "message": "Something went wrong"
        }), 500
    finally:
        if cursor:
            cursor.close()
        if con:
            con.close()


def deactive_discount_items():
    logger.info("Entered in deactive_items function")
    con = None
    cursor = None
    try:
        logger.info("Connecting to database")
        con = get_db_connection(DISCOUNT_DB)
        logger.info("Database connection successful")
        cursor = con.cursor()
        logger.info("Calling Update Query")
        today = date.today()
        sql_query = deactive_exp_discount_items()
        logger.info("Executing update query")
        cursor.execute(sql_query, today)
        updated_rows = cursor.rowcount
        con.commit()
        logger.info(
            f"Updated successfully. Rows affected: {updated_rows}"
        )
        return {
            "status": "success",
            "message": "Items updated successfully",
            "updated_rows": updated_rows
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
            "Database error while updating discount"
        )
        raise
    except Exception:
        if con:
            con.rollback()
        logger.exception(
            "Unexpected error while updating discount"
        )
        raise
    finally:
        if cursor:
            cursor.close()
        if con:
            con.close()

def get_discounts():
    logger.info("Enter into get discount function")
    con = None
    cursor = None
    try:
        data = request.get_json()
        logger.info("Connecting to database")
        con = get_db_connection("DISCOUNT_DATABASE")
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
        sql_query = get_item_discount_details()
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
            "Database error while updating discount"
        )
        raise
    except Exception:
        if con:
            con.rollback()
        logger.exception(
            "Unexpected error while updating discount"
        )
        raise
    finally:
        if cursor:
            cursor.close()
        if con:
            con.close()