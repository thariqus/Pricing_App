import os
import pymysql
from dotenv import load_dotenv


load_dotenv()


PRICING_DB = os.getenv("DB_P_NAME")
DISCOUNT_DB = os.getenv("DB_D_NAME")


def get_db_connection(database=None):
    if database is ...:
        database = PRICING_DB
    try:
        connection = pymysql.connect(
            host=os.getenv("DB_HOST", "localhost"),
            port=int(os.getenv("DB_PORT", 3306)),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            database=database,
            cursorclass=pymysql.cursors.DictCursor,
            connect_timeout=int(
                os.getenv("DB_CONNECT_TIMEOUT", 10)
            ),
            read_timeout=int(
                os.getenv("DB_READ_TIMEOUT", 30)
            ),
            write_timeout=int(
                os.getenv("DB_WRITE_TIMEOUT", 30)
            ),
        )
        return connection
    except pymysql.MySQLError as e:
        raise ConnectionError(
            f"Database connection failed: {e}"
        ) from e