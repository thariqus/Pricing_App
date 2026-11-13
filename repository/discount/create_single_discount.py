from flask import request, jsonify
import pymysql
from repository.mysql_connection import get_db_connection
from utils.log_error import logger
from repository.query import (
    insert_discount_query,
    get_latest_discount_version_id_query,
    insert_discount_version_query,
    deactivate_discount_combination_query,
)
from data.structure.deactivation_combination import COMBINATION_COLUMNS as combination
from datetime import datetime
from repository.discount.create_log import write_log
from data.error_codes import (
    INITIATING_FUNCTION,
    BAD_REQUEST,
    SUCCESS,
    SERVICE_UNAVAILABLE,
    INTERNAL_SERVER_ERROR,
    NOT_IMPLEMENTED
)
import os

LOG_SOURCE = "repository"

DISCOUNT_DB = os.getenv("DB_D_NAME")


def _parse_dt(value):
    """Dates arrive as 'YYYY-MM-DD HH:MM:SS' (utils.date_converter.convert_datetime)."""
    if not value:
        return None
    if isinstance(value, datetime):
        return value
    return datetime.strptime(str(value).strip(), "%Y-%m-%d %H:%M:%S")


def _respond(body, log_type, status, context, message_code, is_error, response_message=None, ipaddress=None):
    """Write the log row, then return the JSON response."""
    write_log(
        custom_message=context,
        response_message=response_message or body.get("message"),
        source=LOG_SOURCE,
        log_type=log_type,
        message_code=message_code,
        log_status=status,
        info=not is_error,
        error=is_error,
        ipaddress=ipaddress
    )
    return jsonify(body), status


def create_single_discount(data):
    con = None
    cursor = None
    context = "Single Item Discount"
    log_type = "Create Single Discount"
    ipaddress = request.remote_addr

    write_log(
        custom_message="Entered in single item discount function",
        ipaddress=ipaddress,
        response_message="",
        source=LOG_SOURCE,
        log_type=log_type,
        message_code=f"PP{INITIATING_FUNCTION}",
        log_status=INITIATING_FUNCTION,
        info=True,
        error=False
    )

    try:
        if not data:
            return _respond(
                body={
                    "status": "error",
                    "message": "Request data is empty or invalid"
                },
                log_type=log_type,
                status=BAD_REQUEST,
                context=context,
                message_code=f"PP{BAD_REQUEST}",
                is_error=True,
                response_message="Request data is empty or invalid",
                ipaddress=ipaddress
            )

        con = get_db_connection(DISCOUNT_DB)
        cursor = con.cursor()

        cursor.execute(get_latest_discount_version_id_query())
        row = cursor.fetchone()

        latest = (
            row["version_id"] if isinstance(row, dict) else row[0]
        ) if row else None

        version_id = (latest or 0) + 1

        # 1. Active is decided by the dates, not by the grid's tick:
        #    already started (and not ended) -> active now, replacing the old discount
        #    starts in the future            -> inactive; the activation scheduler turns it on
        now = datetime.now()
        start = _parse_dt(data.get("starting_date"))
        end = _parse_dt(data.get("ending_date"))
        is_live = (start is None or start <= now) and (end is None or end >= now)

        if is_live:
            deact_sql, deact_params = deactivate_discount_combination_query(data, combination)
            cursor.execute(deact_sql, deact_params)

        data["active"] = 1 if is_live else 0

        # 2. Insert the discount row, stamped with its version so stores can pull it
        data["version_id"] = version_id
        sql_query, params = insert_discount_query(data)
        cursor.execute(sql_query, params)
        inserted_id = cursor.lastrowid

        if not inserted_id:
            con.rollback()
            return _respond(
                body={
                    "status": "error",
                    "message": "Discount could not be created"
                },
                log_type=log_type,
                status=INTERNAL_SERVER_ERROR,
                context=context,
                message_code=f"PP{INTERNAL_SERVER_ERROR}",
                is_error=True,
                response_message="Discount could not be created",
                ipaddress=ipaddress
            )

        # 2. Record the version, once, after the discount row succeeds
        version_sql, version_params = insert_discount_version_query({
            "id": version_id,
            "file_name": "",
            "record_count": 1,
        })
        cursor.execute(version_sql, version_params)

        con.commit()

        return _respond(
            body={"data": inserted_id},
            log_type=log_type,
            status=SUCCESS,
            context=context,
            message_code=f"PP{SUCCESS}",
            is_error=False,
            response_message="Discount created successfully",
            ipaddress=ipaddress
        )

    except ConnectionError as e:
        if con:
            con.rollback()
        logger.exception("Database connection error while creating discount")
        return _respond(
            body={
                "status": "error",
                "message": "Unable to connect to database",
                "error": str(e)
            },
            log_type=log_type,
            status=SERVICE_UNAVAILABLE,
            context=context,
            message_code=f"PC{SERVICE_UNAVAILABLE}",
            is_error=True,
            response_message=str(e),
            ipaddress=ipaddress
        )

    except pymysql.MySQLError as e:
        if con:
            con.rollback()
        logger.exception("Database error while creating discount")
        return _respond(
            body={
                "status": "error",
                "message": "Database error",
                "error": str(e)
            },
            log_type=log_type,
            status=INTERNAL_SERVER_ERROR,
            context=context,
            message_code=f"PC{INTERNAL_SERVER_ERROR}",
            is_error=True,
            response_message=str(e),
            ipaddress=ipaddress
        )

    except Exception as e:
        if con:
            con.rollback()
        logger.exception("Unexpected error while creating discount")
        return _respond(
            body={
                "status": "error",
                "message": "Something went wrong",
                "error": str(e)
            },
            log_type=log_type,
            status=NOT_IMPLEMENTED,
            context=context,
            message_code=f"PC{NOT_IMPLEMENTED}",
            is_error=True,
            response_message=str(e),
            ipaddress=ipaddress
        )

    finally:
        if cursor:
            cursor.close()
        if con:
            con.close()