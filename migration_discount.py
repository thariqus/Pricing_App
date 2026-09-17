import os
from dotenv import load_dotenv
from database.mysql_connection import get_db_connection
from database.query import (
    create_pricing_database_query,
    create_discount_table_query,
    create_discount_location_query,
    create_discount_distribution_channel_query,
    create_discount_priority_query,
    create_discount_currency_query,
    create_discount_transportation_zone_query,
    create_discount_uom_query
) 
 
load_dotenv()
 
DB_NAME = os.getenv("DISCOUNT_DB")
DISCOUNT_TABLE = os.getenv("DISCOUNT_TABLE")
 
 
def create_database():
    con = get_db_connection()
    try:
        with con.cursor() as cursor:
            cursor.execute(create_pricing_database_query(DB_NAME))
        con.commit()
    finally:
        con.close()
 
 
def create_discount_table():
    con = get_db_connection(DB_NAME)
    try:
        with con.cursor() as cursor:
            cursor.execute(create_discount_table_query(DISCOUNT_TABLE))
        con.commit()
    finally:
        con.close()
 
 
def create_discount_submaster():
    """
    Create separate master tables for discount lookup values:
    location,
    distribution channel,
    priority,
    currency,
    transportation zone,
    unit of measure.
    """
    con = get_db_connection(DB_NAME)
    try:
        with con.cursor() as cursor:
            # Location
            cursor.execute(create_discount_location_query())
            # Distribution Channel
            cursor.execute(create_discount_distribution_channel_query())
            # Priority
            cursor.execute(create_discount_priority_query())
            # Currency
            cursor.execute(create_discount_currency_query())
            # Transportation Zone
            cursor.execute(create_discount_transportation_zone_query())
            # Unit of Measure
            cursor.execute(create_discount_uom_query())
        con.commit()
    finally:
        con.close()
 
 
if __name__ == "__main__":
    create_database()
    create_discount_table()
    create_discount_submaster()
 