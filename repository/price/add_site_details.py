from flask import request
from repository.mysql_connection import get_db_connection
import os
import pymysql
from repository.query import insert_site_settings, select_one_sites
from utils.log_response import _respond
from data.error_codes import INITIATING_FUNCTION, BAD_REQUEST, SUCCESS, SERVICE_UNAVAILABLE, INTERNAL_SERVER_ERROR, NOT_IMPLEMENTED, CREATED
from data.response import marshal_response_msg

PRICE_DB = os.getenv("DB_P_NAME")

def response_log(custom_message, code, error, response_message=None):
    return _respond(
        body={},
        custom_message=custom_message,
        ipaddress=request.remote_addr,
        response_message=response_message,
        source="repository",
        log_type="Add site details",
        message_code=f"PP{code}",
        log_status=code,
        error=error
    )


def add_site_details(data):
    con = None
    cursor = None
    response_log("Entered in add site details function", INITIATING_FUNCTION, False)
    try:
        # Database connection
        con = get_db_connection(PRICE_DB)
        cursor = con.cursor()
        # Execute query
        result = []

        inserted_count = 0
        for sites in data['sites']:
            select_sql, select_params = select_one_sites(sites['location'])
            cursor.execute(select_sql, select_params)
            site_datas = cursor.fetchall()

            if len(site_datas) > 0:
                result.append(sites['location'])
                continue
            else:
                sql_query, params = insert_site_settings(sites)
                cursor.execute(sql_query, params)
                inserted_count += cursor.rowcount
        con.commit()

        if inserted_count < 0:
            return ("", {"error" : True, "error_code" : INTERNAL_SERVER_ERROR})
        
        response_log(f"{inserted_count} Sites created successfully", SUCCESS, False)

        response_log("Site setting completed successfully", SUCCESS, False)

        return ({
            "data" : inserted_count,
            "message_result" : result
            }, {"error" : False, "error_code" : SUCCESS})

    except ConnectionError as e:
        mysql_error_code = e.args[0] if e.args else None
        http_status = SERVICE_UNAVAILABLE if mysql_error_code in (2002, 2003, 2006, 2013) else INTERNAL_SERVER_ERROR

        response_log("Databse connection error, unable to connect database", http_status, True, str(e))

        return ("", {"error" : True, "error_code" : http_status})
    
    except pymysql.MySQLError as e:
        mysql_error_code = e.args[0] if e.args else None
        http_status = SERVICE_UNAVAILABLE if mysql_error_code in (2002, 2003, 2006, 2013) else INTERNAL_SERVER_ERROR

        response_log("Database error while fetching prices", http_status, True, str(e))
        
        return ("", {"error" : True, "error_code" : http_status})
    
    except Exception as e:
        response_log("Unexpected error while fetching prices data", NOT_IMPLEMENTED, True, str(e))
        
        return ("", {"error" : True, "error_code" : NOT_IMPLEMENTED})

    finally:
        if cursor:
            cursor.close()
        if con:
            con.close()