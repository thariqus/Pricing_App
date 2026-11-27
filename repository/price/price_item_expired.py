import pymysql
from data.error_codes import INITIATING_FUNCTION, SERVICE_UNAVAILABLE, INTERNAL_SERVER_ERROR, NOT_IMPLEMENTED, SUCCESS
from utils.log_response import _respond
from repository.mysql_connection import get_db_connection
from repository.query import insert_expired_price_query
import os

PRICE_DB = os.getenv("DB_P_NAME")


def response_log(custom_message, code, error, response_message=None):
    return _respond(
        body={},
        custom_message=custom_message,
        ipaddress="",
        response_message=response_message,
        source="repository",
        log_type="Moved expired price items",
        message_code=f"PP{code}",
        log_status=code,
        error=error
    )

def price_item_expired(data):
    con = None
    cursor = None
    response_log("Enter into create expired price items function", INITIATING_FUNCTION, False)
    try:
        con = get_db_connection(PRICE_DB)
        cursor = con.cursor()

        # Get query and parameters
        expired_price_logs = [
            (
                row['active'],
                row['condition_type'],
                row['item_no'],
                row['customer'],
                row['customer_grp'],
                row['customer_hierarchy'],
                row['distribution_channel_code'],
                row['location_code'],
                row['priority'],
                row['currency'],
                row['sales_price'],
                row['uom'],
                row['minimum_quantity'],
                row['starting_date'],
                row['ending_date'],
                row['lower_limit'],
                row['upper_limit'],
                row['transportation_zone_code'],
                row['map'],
                row['change_type'],
                row['updated_from_sap'],
                row['sales_division_code'],
                row['offer_article'],
                row['price_with_tax'],
                row['tax_percent'],
                row['version_id']
            )
            for row in data
        ]
        query, params = insert_expired_price_query(expired_price_logs)

        # Execute query
        cursor.executemany(query, params)

        # Check whether the site exists
        if cursor.rowcount != len(expired_price_logs):
            con.rollback()
            response_log("Something went wrong, can't move the expired price items", INTERNAL_SERVER_ERROR, True)
            return ("", {"error" : True, "error_code" : INTERNAL_SERVER_ERROR})
        else:
            response_log(f"Successfully moved {cursor.rowcount} price items", SUCCESS, False)
            # Commit changes
            con.commit()

            response_log("Create expired price items completed", SUCCESS, False)
            return (cursor.rowcount, {"error" : False, "error_code" : SUCCESS})
    except ConnectionError as e:
        con.rollback()
        mysql_error_code = e.args[0] if e.args else None
        http_status = SERVICE_UNAVAILABLE if mysql_error_code in (2002, 2003, 2006, 2013) else INTERNAL_SERVER_ERROR

        response_log("Databse connection error, unable to connect database", http_status, True, str(e))

        return ("", {"error" : True, "error_code" : http_status})
    
    except pymysql.MySQLError as e:
        con.rollback()
        mysql_error_code = e.args[0] if e.args else None
        http_status = SERVICE_UNAVAILABLE if mysql_error_code in (2002, 2003, 2006, 2013) else INTERNAL_SERVER_ERROR

        response_log("Database error while insert expired price items", http_status, True, str(e))
        
        return ("", {"error" : True, "error_code" : http_status})
    
    except Exception as e:
        con.rollback()
        response_log("Unexpected error while insert expired price items", NOT_IMPLEMENTED, True, str(e))
        
        return ("", {"error" : True, "error_code" : NOT_IMPLEMENTED})
    finally:
        if cursor:
            cursor.close()

        if con:
            con.close()
