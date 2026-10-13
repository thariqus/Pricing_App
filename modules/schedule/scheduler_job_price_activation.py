import os
import time
from datetime import datetime
from repository.mysql_connection import get_db_connection
from repository.query import (
    get_pending_activation_query,
    get_active_same_combination_query,
    deactivate_price_by_ids_query,
    activate_price_by_id_query,
)
from data.structure.deactivation_combination import COMBINATION_COLUMNS as combination
from utils.log_error import logger

PRICE_DB = os.getenv("DB_P_NAME")


def check_pending_activation():
    con = None
    try:
        con = get_db_connection(PRICE_DB)
        with con.cursor() as cursor:
            now = datetime.now()
            cursor.execute(get_pending_activation_query(), (now, now))
            rows = cursor.fetchall()
            logger.info("Pending activation: %s price(s)", len(rows))

            # latest uploaded first, so it wins within the same combination
            for row in sorted(rows, key=lambda r: r["id"], reverse=True):
                sql_query, params = get_active_same_combination_query(row, combination)
                cursor.execute(sql_query, params)
                active_rows = cursor.fetchall()
                print(f"Active with same combination: {len(active_rows)}", flush=True)

                expired = [a for a in active_rows if a["ending_date"] < now]
                print(f"Expired active with same combination: {len(expired)}", flush=True)

                # still a valid active price -> leave the new one inactive
                if len(expired) < len(active_rows):
                    continue

                if expired:
                    sql_query, params = deactivate_price_by_ids_query([a["id"] for a in expired])
                    cursor.execute(sql_query, params)
                    print(f"Deactivated: {[a['id'] for a in expired]}", flush=True)

                sql_query, params = activate_price_by_id_query(row["id"])
                cursor.execute(sql_query, params)
                print(f"Activated: {row['id']}", flush=True)

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