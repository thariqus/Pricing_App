import os
from dotenv import load_dotenv
from database.mysql_connection import get_db_connection
from database.query import create_pricing_database_query, create_table_query 
from database.tables import PRICING_TABLE, PRICE_LOCATION, PRICING_DISTRIBUTION_CHANNEL, PRICING_PRIORITY,PRICING_CURRENCY, PRICING_TRANSPORTATION_ZONE, PRICING_UOM
from database.fields import Pricing_Table, Pricing_Location, Pricing_Distribution_Channel, Pricing_Priority, Pricing_Currency, Pricing_Transportation_Zone, Pricing_UOM
from utils.log_error import logger
 
load_dotenv()
DB_NAME = os.getenv("DB_P_NAME")
 
 
def create_database():
    con = None
    try:
        con = get_db_connection()
        with con.cursor() as cursor:
            cursor.execute(create_pricing_database_query(DB_NAME))
        con.commit()
        logger.info("Database '%s' successfully created",DB_NAME)
    except Exception:
        logger.exception("Failed to create database '%s'",DB_NAME)
        raise
    finally:
        if con:
            con.close()


def create_pricing_table():
    con = None
    try:
        con = get_db_connection(DB_NAME)
        with con.cursor() as cursor:
            cursor.execute(create_table_query(PRICING_TABLE, Pricing_Table))
        con.commit()
        logger.info(
            "Table '%s' successfully created",PRICING_TABLE)
    except Exception:
        logger.exception("Failed to create table '%s'",PRICING_TABLE)
        raise
    finally:
        if con:
            con.close()


def create_pricing_location():
    con = None
    try:
        con = get_db_connection(DB_NAME)
        with con.cursor() as cursor:
            cursor.execute(create_table_query(PRICE_LOCATION,Pricing_Location))
        con.commit()
        logger.info("Table '%s' successfully created",PRICE_LOCATION)
    except Exception:
        logger.exception("Failed to create table '%s'",PRICE_LOCATION)
        raise
    finally:
        if con:
            con.close()


def create_pricing_distribution_channel():
    con = None
    try:
        con = get_db_connection(DB_NAME)
        with con.cursor() as cursor:
            cursor.execute(create_table_query(PRICING_DISTRIBUTION_CHANNEL,Pricing_Distribution_Channel))
        con.commit()
        logger.info("Table '%s' successfully created",PRICING_DISTRIBUTION_CHANNEL)
    except Exception:
        logger.exception("Failed to create table '%s'",PRICING_DISTRIBUTION_CHANNEL)
        raise
    finally:
        if con:
            con.close()


def create_pricing_priority():
    con = None
    try:
        con = get_db_connection(DB_NAME)
        with con.cursor() as cursor:
            cursor.execute(create_table_query(PRICING_PRIORITY,Pricing_Priority))
        con.commit()
        logger.info("Table '%s' successfully created",PRICING_PRIORITY)
    except Exception:
        logger.exception("Failed to create table '%s'",PRICING_PRIORITY)
        raise
    finally:
        if con:
            con.close()


def create_pricing_currency():
    con = None
    try:
        con = get_db_connection(DB_NAME)
        with con.cursor() as cursor:
            cursor.execute(create_table_query(PRICING_CURRENCY,Pricing_Currency))
        con.commit()
        logger.info("Table '%s' successfully created",PRICING_CURRENCY)
    except Exception:
        logger.exception("Failed to create table '%s'",PRICING_CURRENCY)
        raise
    finally:
        if con:
            con.close()


def create_pricing_transportation_zone():
    con = None
    try:
        con = get_db_connection(DB_NAME)
        with con.cursor() as cursor:
            cursor.execute(create_table_query(PRICING_TRANSPORTATION_ZONE,Pricing_Transportation_Zone))
        con.commit()
        logger.info("Table '%s' successfully created",PRICING_TRANSPORTATION_ZONE)
    except Exception:
        logger.exception("Failed to create table '%s'",PRICING_TRANSPORTATION_ZONE)
        raise
    finally:
        if con:
            con.close()


def create_pricing_uom():
    con = None
    try:
        con = get_db_connection(DB_NAME)
        with con.cursor() as cursor:
            cursor.execute(create_table_query(PRICING_UOM,Pricing_UOM))
        con.commit()
        logger.info("Table '%s' successfully created",PRICING_UOM)
    except Exception:
        logger.exception("Failed to create table '%s'",PRICING_UOM)
        raise
    finally:
        if con:
            con.close()


if __name__ == "__main__":
    create_database()
    create_pricing_table()
    create_pricing_location()
    create_pricing_distribution_channel()
    create_pricing_priority()
    create_pricing_currency()
    create_pricing_transportation_zone()
    create_pricing_uom()
 