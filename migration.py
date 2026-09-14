import os

import pymysql
from dotenv import load_dotenv


load_dotenv()


def create_database():

    con = pymysql.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", 3306)),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),

        connect_timeout=int(os.getenv("DB_CONNECT_TIMEOUT", 10)),
        read_timeout=int(os.getenv("DB_READ_TIMEOUT", 30)),
        write_timeout=int(os.getenv("DB_WRITE_TIMEOUT", 30)),
    )

    try:

        cursor = con.cursor()

        query = """
            CREATE DATABASE IF NOT EXISTS PRICING_DATABASE
        """

        cursor.execute(query)

        print("Database 'pricing_database' is ready.")

    finally:

        cursor.close()
        con.close()


def create_item_number_table():

    con = pymysql.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", 3306)),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database="PRICING_DATABASE",

        connect_timeout=int(os.getenv("DB_CONNECT_TIMEOUT", 10)),
        read_timeout=int(os.getenv("DB_READ_TIMEOUT", 30)),
        write_timeout=int(os.getenv("DB_WRITE_TIMEOUT", 30)),
    )

    try:

        cursor = con.cursor()

        query = """

            CREATE TABLE IF NOT EXISTS PRICING_TABLE (

                id INT AUTO_INCREMENT PRIMARY KEY,

                active BOOLEAN,

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

                tax_percent FLOAT

            )

        """

        cursor.execute(query)

        print("Table 'item_number' is ready.")

    finally:

        cursor.close()
        con.close()


if __name__ == "__main__":

    create_database()
    create_item_number_table()