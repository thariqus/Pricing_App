import os
import time
from datetime import datetime
from repository.mysql_connection import get_db_connection
from repository.price.fetch_store_pricing_version import get_latest_version_id
from repository.query import (
    get_pending_activation_query,
    get_active_same_combination_query,
    deactivate_price_by_ids_query,
    activate_price_by_id_query,
    select_all_prices_scheduler,
    insert_version_query
)
from data.structure.deactivation_combination import COMBINATION_COLUMNS as combination
from utils.log_error import logger
from data.data_processing._to_datetime import _to_datetime

IS_CENTRAL = os.getenv("IS_CENTRAL")
PRICE_DB = os.getenv("DB_P_NAME")


def check_pending_activation():
    con = None
    try:
        con = get_db_connection(PRICE_DB)
        with con.cursor() as cursor:
            now = datetime.now()

            ho_version = int(get_latest_version_id() or 0)
            latest_version = ho_version + 1

            cursor.execute(get_pending_activation_query(), (now, now))
            rows = cursor.fetchall()
            logger.info("Expired item price(s): %s", len(rows))

            cursor.execute(select_all_prices_scheduler())
            all_prices = cursor.fetchall()
            expired = [a for a in all_prices if _to_datetime(a["ending_date"]) < now]
            if expired:
                sql_query, params = deactivate_price_by_ids_query([a["id"] for a in expired])
                cursor.execute(sql_query, params)

            # latest uploaded first, so it wins within the same combination
            for row in sorted(rows, key=lambda r: r["id"]):   # oldest first, newest processed last so it wins
                sql_query, params = get_active_same_combination_query(row, combination)
                cursor.execute(sql_query, params)
                active_rows = cursor.fetchall()

                active_data = max([ad for ad in active_rows if _to_datetime(ad['starting_date']) < datetime.now() and _to_datetime(ad['ending_date']) > datetime.now()], key=lambda ad: ad['id'],default=None)

                # active_data = max((ad for ad in active_rows if _to_datetime(ad['starting_date']) < datetime.now()),key=lambda ad: ad['starting_date'],default=None)

                ids_to_deactivate = [a["id"] for a in active_rows if a["id"] != active_data['id']]

                if ids_to_deactivate:
                    sql_query, params = deactivate_price_by_ids_query(ids_to_deactivate)
                    cursor.execute(sql_query, params)


                if IS_CENTRAL == "1":
                    sql_query, params = activate_price_by_id_query(active_data['id'], latest_version)
                    cursor.execute(sql_query, params)
                    if cursor.rowcount > 0:
                        version_sql, version_params = insert_version_query({
                            "id": latest_version,
                            "file_name": "",
                            "record_count": 1,
                        })
        
                        cursor.execute(version_sql, version_params)

        con.commit()
        return rows
    except Exception:
        if con:
            con.rollback()
        logger.exception("Failed to check pending activation")
        return []
    finally:
        if con:
            con.close()


def run_scheduler(interval=10):
    while True:
        start = time.monotonic()
        check_pending_activation()
        time.sleep(max(0, interval - (time.monotonic() - start)))