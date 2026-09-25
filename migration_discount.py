import os
from dotenv import load_dotenv
from repository.mysql_connection import get_db_connection
from repository.query import create_pricing_database_query,create_table_query
from repository.tables import DISCOUNT_TABLE,DISCOUNT_LOCATION,DISCOUNT_DISTRIBUTION_CHANNEL,DISCOUNT_PRIORITY,DISCOUNT_CURRENCY,DISCOUNT_TRANSPORATION_ZONE,DISCOUNT_UOM
from repository.fields import Discount_Table,Discount_Location,Discount_Distribution_Channel,Discount_Priority,Discount_Currency,Discount_Transportation_Zone,Discount_UOM
from utils.log_error import logger
load_dotenv()

DB_NAME = os.getenv("DB_D_NAME")

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

def create_discount_table():
    con = None
    try:
        con = get_db_connection(DB_NAME)
        with con.cursor() as cursor:
            cursor.execute(create_table_query(DISCOUNT_TABLE,Discount_Table))
        con.commit()
        logger.info("Table '%s' successfully created",DISCOUNT_TABLE)
    except Exception:
        logger.exception("Failed to create table '%s'",DISCOUNT_TABLE)
        raise
    finally:
        if con:
            con.close()

def create_discount_location():
    con = None
    try:
        con = get_db_connection(DB_NAME)
        with con.cursor() as cursor:
            cursor.execute(create_table_query(DISCOUNT_LOCATION,Discount_Location))
        con.commit()
        logger.info("Table '%s' successfully created",DISCOUNT_LOCATION)
    except Exception:
        logger.exception("Failed to create table '%s'",DISCOUNT_LOCATION)
        raise
    finally:
        if con:
            con.close()

def create_discount_distribution_channel():
    con = None
    try:
        con = get_db_connection(DB_NAME)
        with con.cursor() as cursor:
            cursor.execute(create_table_query(DISCOUNT_DISTRIBUTION_CHANNEL,Discount_Distribution_Channel))
        con.commit()
        logger.info("Table '%s' successfully created",DISCOUNT_DISTRIBUTION_CHANNEL)
    except Exception:
        logger.exception("Failed to create table '%s'",DISCOUNT_DISTRIBUTION_CHANNEL)
        raise
    finally:
        if con:
            con.close()

def create_discount_priority():
    con = None
    try:
        con = get_db_connection(DB_NAME)
        with con.cursor() as cursor:
            cursor.execute(create_table_query(DISCOUNT_PRIORITY,Discount_Priority))
        con.commit()
        logger.info("Table '%s' successfully created",DISCOUNT_PRIORITY)
    except Exception:
        logger.exception("Failed to create table '%s'",DISCOUNT_PRIORITY        )
        raise
    finally:
        if con:
            con.close()

def create_discount_currency():
    con = None
    try:
        con = get_db_connection(DB_NAME)
        with con.cursor() as cursor:
            cursor.execute(create_table_query(DISCOUNT_CURRENCY,Discount_Currency))
        con.commit()
        logger.info("Table '%s' successfully created",DISCOUNT_CURRENCY)
    except Exception:
        logger.exception("Failed to create table '%s'",DISCOUNT_CURRENCY)
        raise
    finally:
        if con:
            con.close()

def create_discount_transportation_zone():
    con = None
    try:
        con = get_db_connection(DB_NAME)
        with con.cursor() as cursor:
            cursor.execute(create_table_query(DISCOUNT_TRANSPORATION_ZONE,Discount_Transportation_Zone))
        con.commit()
        logger.info("Table '%s' successfully created",DISCOUNT_TRANSPORATION_ZONE)
    except Exception:
        logger.exception("Failed to create table '%s'",DISCOUNT_TRANSPORATION_ZONE)
        raise
    finally:
        if con:
            con.close()

def create_discount_uom():
    con = None
    try:
        con = get_db_connection(DB_NAME)
        with con.cursor() as cursor:
            cursor.execute(create_table_query(DISCOUNT_UOM,Discount_UOM))
        con.commit()
        logger.info("Table '%s' successfully created",DISCOUNT_UOM)
    except Exception:
        logger.exception("Failed to create table '%s'",DISCOUNT_UOM)
        raise
    finally:
        if con:
            con.close()

if __name__ == "__main__":
        create_database()
        create_discount_table()
        create_discount_location()
        create_discount_distribution_channel()
        create_discount_priority()
        create_discount_currency()
        create_discount_transportation_zone()
        create_discount_uom()