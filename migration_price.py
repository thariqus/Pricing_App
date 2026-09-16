import os
 
import pymysql
from dotenv import load_dotenv
from database.mysql_connection import get_db_connection
from database.query import (
    create_pricing_database_query, 
    create_pricing_table_query, 
    create_pricing_location_query, 
    create_pricing_distribution_channel_query, 
    create_pricing_priority_query, 
    create_pricing_currency_query, 
    create_pricing_transportation_zone_query, 
    create_pricing_uom_query
    )
 
load_dotenv()
 
DB_NAME = os.getenv("PRICING_DB")
PRICING_TABLE = os.getenv("PRICING_TABLE")
 
 
def create_database():
    con = get_db_connection()
    try:
        with con.cursor() as cursor:
            cursor.execute(create_pricing_database_query(DB_NAME))
        con.commit()
    finally:
        con.close()
 
 
def create_pricing_table():
    con = get_db_connection()
    try:
        with con.cursor() as cursor:
            cursor.execute(create_pricing_table_query(PRICING_TABLE))
        con.commit()
    finally:
        con.close()
 
 
def create_pricing_submaster():
 
    """
    Create separate master tables for pricing lookup values:
    location,
    distribution channel,
    priority,
    currency,
    transportation zone,
    unit of measure.
    """
 
    con = get_db_connection()
 
    try:
 
        with con.cursor() as cursor:
 
            # Location
            cursor.execute(create_pricing_location_query())
 
            # Distribution Channel
            cursor.execute(create_pricing_distribution_channel_query())
 
            # Priority
            cursor.execute(create_pricing_priority_query())
 
            # Currency
            cursor.execute(create_pricing_currency_query())
 
            # Transportation Zone
            cursor.execute(create_pricing_transportation_zone_query())
 
            # Unit of Measure
            cursor.execute(create_pricing_uom_query())
 
        con.commit()
 
    finally:
 
        con.close()
 
 
if __name__ == "__main__":
    create_database()
    create_pricing_table()
    create_pricing_submaster()
 