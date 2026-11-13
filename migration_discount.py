import os
from datetime import datetime
from dotenv import load_dotenv
from repository.mysql_connection import get_db_connection
from repository.query import (
    create_pricing_database_query,
    create_table_query,
    create_version_table_query,
)
from repository.tables import (
    DISCOUNT_TABLE,
    DISCOUNT_LOCATION,
    DISCOUNT_DISTRIBUTION_CHANNEL,
    DISCOUNT_PRIORITY,
    DISCOUNT_CURRENCY,
    DISCOUNT_TRANSPORATION_ZONE,
    DISCOUNT_UOM,
    DISCOUNT_VERSION,
    DISCOUNT_SETTING,
    DISCOUNT_SETTING_SITE,
    LOG_MESSAGE,
    REPLICATION_VERSION,
)
from repository.fields import (
    Discount_Table,
    Discount_Location,
    Discount_Distribution_Channel,
    Discount_Priority,
    Discount_Currency,
    Discount_Transportation_Zone,
    Discount_UOM,
    Discount_Version,
    Discount_Setting,
    Discount_Setting_Site,
    log_message,
    replication_version,
)
from utils.log_error import logger

load_dotenv()

DB_NAME = os.getenv("DB_D_NAME")


def now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def create_database():
    con = None
    try:
        con = get_db_connection()
        with con.cursor() as cursor:
            cursor.execute(create_pricing_database_query(DB_NAME))
        con.commit()
        logger.info("[%s] Database '%s' successfully created", now(), DB_NAME)
    except Exception:
        logger.exception("[%s] Failed to create database '%s'", now(), DB_NAME)
        raise
    finally:
        if con:
            con.close()


def create_discount_table():
    con = None
    try:
        con = get_db_connection(DB_NAME)
        with con.cursor() as cursor:
            cursor.execute(create_table_query(DISCOUNT_TABLE, Discount_Table))
        con.commit()
        logger.info("[%s] Table '%s' successfully created", now(), DISCOUNT_TABLE)
    except Exception:
        logger.exception("[%s] Failed to create table '%s'", now(), DISCOUNT_TABLE)
        raise
    finally:
        if con:
            con.close()


def create_discount_location():
    con = None
    try:
        con = get_db_connection(DB_NAME)
        with con.cursor() as cursor:
            cursor.execute(create_table_query(DISCOUNT_LOCATION, Discount_Location))
        con.commit()
        logger.info("[%s] Table '%s' successfully created", now(), DISCOUNT_LOCATION)
    except Exception:
        logger.exception("[%s] Failed to create table '%s'", now(), DISCOUNT_LOCATION)
        raise
    finally:
        if con:
            con.close()


def create_discount_distribution_channel():
    con = None
    try:
        con = get_db_connection(DB_NAME)
        with con.cursor() as cursor:
            cursor.execute(create_table_query(DISCOUNT_DISTRIBUTION_CHANNEL, Discount_Distribution_Channel))
        con.commit()
        logger.info("[%s] Table '%s' successfully created", now(), DISCOUNT_DISTRIBUTION_CHANNEL)
    except Exception:
        logger.exception("[%s] Failed to create table '%s'", now(), DISCOUNT_DISTRIBUTION_CHANNEL)
        raise
    finally:
        if con:
            con.close()


def create_discount_priority():
    con = None
    try:
        con = get_db_connection(DB_NAME)
        with con.cursor() as cursor:
            cursor.execute(create_table_query(DISCOUNT_PRIORITY, Discount_Priority))
        con.commit()
        logger.info("[%s] Table '%s' successfully created", now(), DISCOUNT_PRIORITY)
    except Exception:
        logger.exception("[%s] Failed to create table '%s'", now(), DISCOUNT_PRIORITY)
        raise
    finally:
        if con:
            con.close()


def create_discount_currency():
    con = None
    try:
        con = get_db_connection(DB_NAME)
        with con.cursor() as cursor:
            cursor.execute(create_table_query(DISCOUNT_CURRENCY, Discount_Currency))
        con.commit()
        logger.info("[%s] Table '%s' successfully created", now(), DISCOUNT_CURRENCY)
    except Exception:
        logger.exception("[%s] Failed to create table '%s'", now(), DISCOUNT_CURRENCY)
        raise
    finally:
        if con:
            con.close()


def create_discount_transportation_zone():
    con = None
    try:
        con = get_db_connection(DB_NAME)
        with con.cursor() as cursor:
            cursor.execute(create_table_query(DISCOUNT_TRANSPORATION_ZONE, Discount_Transportation_Zone))
        con.commit()
        logger.info("[%s] Table '%s' successfully created", now(), DISCOUNT_TRANSPORATION_ZONE)
    except Exception:
        logger.exception("[%s] Failed to create table '%s'", now(), DISCOUNT_TRANSPORATION_ZONE)
        raise
    finally:
        if con:
            con.close()


def create_discount_uom():
    con = None
    try:
        con = get_db_connection(DB_NAME)
        with con.cursor() as cursor:
            cursor.execute(create_table_query(DISCOUNT_UOM, Discount_UOM))
        con.commit()
        logger.info("[%s] Table '%s' successfully created", now(), DISCOUNT_UOM)
    except Exception:
        logger.exception("[%s] Failed to create table '%s'", now(), DISCOUNT_UOM)
        raise
    finally:
        if con:
            con.close()


def create_discount_version():
    con = None
    try:
        con = get_db_connection(DB_NAME)
        with con.cursor() as cursor:
            cursor.execute(create_version_table_query(DISCOUNT_VERSION, Discount_Version))
        con.commit()
        logger.info("Table '%s' successfully created", DISCOUNT_VERSION)
    except Exception:
        logger.exception("Failed to create table '%s'", DISCOUNT_VERSION)
        raise
    finally:
        if con:
            con.close()


def create_discount_log_message():
    con = None
    try:
        con = get_db_connection(DB_NAME)
        with con.cursor() as cursor:
            cursor.execute(create_table_query(LOG_MESSAGE, log_message))
        con.commit()
        logger.info("[%s] Table '%s' successfully created", now(), LOG_MESSAGE)
    except Exception:
        logger.exception("[%s] Failed to create table '%s'", now(), LOG_MESSAGE)
        raise
    finally:
        if con:
            con.close()


def create_discount_setting_tables():
    con = None
    try:
        con = get_db_connection(DB_NAME)
        with con.cursor() as cursor:
            cursor.execute(create_table_query(DISCOUNT_SETTING, Discount_Setting))
            cursor.execute(create_table_query(DISCOUNT_SETTING_SITE, Discount_Setting_Site))
        con.commit()
        logger.info("[%s] Tables '%s' and '%s' successfully created", now(), DISCOUNT_SETTING, DISCOUNT_SETTING_SITE)
    except Exception:
        logger.exception("[%s] Failed to create tables '%s' and '%s'", now(), DISCOUNT_SETTING, DISCOUNT_SETTING_SITE)
        raise
    finally:
        if con:
            con.close()


def create_discount_replication_version():
    con = None
    try:
        con = get_db_connection(DB_NAME)
        with con.cursor() as cursor:
            cursor.execute(create_table_query(REPLICATION_VERSION, replication_version))
        con.commit()
        logger.info("[%s] Table '%s' successfully created", now(), REPLICATION_VERSION)
    except Exception:
        logger.exception("[%s] Failed to create table '%s'", now(), REPLICATION_VERSION)
        raise
    finally:
        if con:
            con.close()

def add_missing_columns():
    """Bring existing tables in line with fields.py. Safe to run repeatedly."""
    statements = [
        f"""ALTER TABLE {DISCOUNT_TABLE}
            MODIFY starting_date DATETIME,
            MODIFY ending_date DATETIME,
            ADD COLUMN IF NOT EXISTS ho_id INT NULL,
            ADD COLUMN IF NOT EXISTS version_id INT NULL,
            ADD INDEX IF NOT EXISTS idx_version_id (version_id)""",
        f"""ALTER TABLE {LOG_MESSAGE}
            ADD COLUMN IF NOT EXISTS ipaddress VARCHAR(100),
            ADD COLUMN IF NOT EXISTS site_details VARCHAR(100),
            ADD COLUMN IF NOT EXISTS `type` VARCHAR(20)""",
    ]
    con = None
    try:
        con = get_db_connection(DB_NAME)
        with con.cursor() as cursor:
            for sql in statements:
                cursor.execute(sql)
        con.commit()
        logger.info("[%s] Existing tables updated", now())
    except Exception:
        logger.exception("[%s] Failed to update existing tables", now())
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
    create_discount_version()
    create_discount_log_message()
    create_discount_setting_tables()
    create_discount_replication_version()
    add_missing_columns()
   