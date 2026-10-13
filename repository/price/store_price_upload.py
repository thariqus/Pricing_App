from repository.query import insert_price_query
from repository.mysql_connection import get_db_connection
from utils.log_error import logger


def insert_store_prices(rows, db_name="PRICING_DATABASE"):
    con = None
    try:
        con = get_db_connection(db_name)
        with con.cursor() as cursor:
            for row in rows:
                data = dict(row)
                # insert_price_query reads customer_group; DB rows have customer_grp
                data.setdefault("customer_group", data.get("customer_grp"))
                sql_query, params = insert_price_query(data)
                cursor.execute(sql_query, params)
        con.commit()
        print(f"Inserted {len(rows)} price(s)", flush=True)
        return len(rows)
    except Exception:
        if con:
            con.rollback()
        logger.exception("Failed to insert store prices")
        return 0
    finally:
        if con:
            con.close()