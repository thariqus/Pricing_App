import os
 
import pymysql
from dotenv import load_dotenv
 
 
load_dotenv()
 
 
def get_db_connection():
 
    try:
 
        connection = pymysql.connect(
            host=os.getenv("DB_HOST", "localhost"),
            port=int(os.getenv("DB_PORT", 3306)),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            database=os.getenv("PRICING_DB"),
 
            cursorclass=pymysql.cursors.DictCursor,
 
            connect_timeout=int(os.getenv("DB_CONNECT_TIMEOUT", 10)),
            read_timeout=int(os.getenv("DB_READ_TIMEOUT", 30)),
            write_timeout=int(os.getenv("DB_WRITE_TIMEOUT", 30)),
        )
 
        return connection
 
    except pymysql.MySQLError as e:
 
        raise ConnectionError(
            f"Database connection failed: {e}"
        ) from e
 