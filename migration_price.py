import os
 
import pymysql
from dotenv import load_dotenv
from database.mysql_connection import get_db_connection,PRICING_DB_CREATION_QUERY
 
load_dotenv()
 
DB_NAME = os.getenv("PRICING_DB")
PRICING_TABLE = os.getenv("PRICING_TABLE")
 
 
def create_database():
    con = get_db_connection()
    try:
        with con.cursor() as cursor:
            cursor.execute(PRICING_DB_CREATION_QUERY)
        con.commit()
        print(f"Database '{DB_NAME}' is ready.")
    finally:
        con.close()
 
 
def create_pricing_table():
    con = get_db_connection()
    try:
        with con.cursor() as cursor:
            cursor.execute(f"""
                CREATE TABLE IF NOT EXISTS {PRICING_TABLE} (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    active BOOLEAN DEFAULT 1,
                    condition_type VARCHAR(100),
                    item_no VARCHAR(100),
                    customer VARCHAR(100),
                    customer_grp INT,
                    customer_hierarchy INT,
                    distribution_channel_code INT,
                    location_code INT,
                    priority INT,
                    currency VARCHAR(100),
                    sales_price FLOAT,
                    unit_of_measure VARCHAR(100),
                    minimum_quantity INT,
                    starting_date DATE,
                    ending_date DATE,
                    lower_limit FLOAT,
                    upper_limit FLOAT,
                    transportation_zone_code VARCHAR(100),
                    map VARCHAR(100),
                    change_type VARCHAR(100),
                    updated_from_sap BOOLEAN,
                    sales_division_code INT,
                    offer_article BOOLEAN,
                    price_with_tax FLOAT,
                    tax_percent FLOAT,
                    KEY idx_item_uom (item_no, unit_of_measure),
                    KEY idx_dates (starting_date, ending_date)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """)
        con.commit()
        print(f"Table '{PRICING_TABLE}' is ready.")
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
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS pricing_location (
 
                    id INT AUTO_INCREMENT PRIMARY KEY,
 
                    location INT NOT NULL,
 
                    is_active TINYINT(1) NOT NULL DEFAULT 1,
 
                    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
 
                    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
                        ON UPDATE CURRENT_TIMESTAMP,
 
                    UNIQUE KEY uq_location (location),
 
                    KEY idx_location_active (location, is_active)
 
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """)
 
            # Distribution Channel
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS pricing_distribution_channel (
 
                    id INT AUTO_INCREMENT PRIMARY KEY,
 
                    distribution_channel_code VARCHAR(20) NOT NULL,
 
                    is_active TINYINT(1) NOT NULL DEFAULT 1,
 
                    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
 
                    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
                        ON UPDATE CURRENT_TIMESTAMP,
 
                    UNIQUE KEY uq_distribution_channel (
                        distribution_channel_code
                    ),
 
                    KEY idx_distribution_channel_active (
                        distribution_channel_code,
                        is_active
                    )
 
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """)
 
            # Priority
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS pricing_priority (
 
                    id INT AUTO_INCREMENT PRIMARY KEY,
 
                    priority INT NOT NULL,
 
                    is_active TINYINT(1) NOT NULL DEFAULT 1,
 
                    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
 
                    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
                        ON UPDATE CURRENT_TIMESTAMP,
 
                    UNIQUE KEY uq_priority (priority),
 
                    KEY idx_priority_active (
                        priority,
                        is_active
                    )
 
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """)
 
            # Currency
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS pricing_currency (
 
                    id INT AUTO_INCREMENT PRIMARY KEY,
 
                    currency VARCHAR(20) NOT NULL,
 
                    is_active TINYINT(1) NOT NULL DEFAULT 1,
 
                    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
 
                    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
                        ON UPDATE CURRENT_TIMESTAMP,
 
                    UNIQUE KEY uq_currency (currency),
 
                    KEY idx_currency_active (
                        currency,
                        is_active
                    )
 
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """)
 
            # Transportation Zone
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS pricing_transportation_zone (
 
                    id INT AUTO_INCREMENT PRIMARY KEY,
 
                    transportation_zone_code VARCHAR(20) NOT NULL,
 
                    is_active TINYINT(1) NOT NULL DEFAULT 1,
 
                    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
 
                    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
                        ON UPDATE CURRENT_TIMESTAMP,
 
                    UNIQUE KEY uq_transportation_zone (
                        transportation_zone_code
                    ),
 
                    KEY idx_transportation_zone_active (
                        transportation_zone_code,
                        is_active
                    )
 
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """)
 
            # Unit of Measure
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS pricing_uom (
 
                    id INT AUTO_INCREMENT PRIMARY KEY,
 
                    UOM VARCHAR(20) NOT NULL,
 
                    is_active TINYINT(1) NOT NULL DEFAULT 1,
 
                    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
 
                    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
                        ON UPDATE CURRENT_TIMESTAMP,
 
                    UNIQUE KEY uq_uom (UOM),
 
                    KEY idx_uom_active (
                        UOM,
                        is_active
                    )
 
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """)
 
        con.commit()
 
        print("Pricing master tables are ready.")
 
    finally:
 
        con.close()
 
 
if __name__ == "__main__":
    create_database()
    create_pricing_table()
    create_pricing_submaster()
 