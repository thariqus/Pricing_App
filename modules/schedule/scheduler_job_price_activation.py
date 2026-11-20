import os
import time
from datetime import datetime
from repository.mysql_connection import get_db_connection
from repository.query import (
    get_pending_activation_query,
    get_pending_discount_activation_query,
    get_active_same_combination_query,
    get_active_same_combination_discount_query,
    deactivate_price_by_ids_query,
    activate_price_by_id_query,
    activate_discount_by_id_query,
    deactivate_discount_by_ids_query,
    deactivate_expired_discounts,
    deactivate_upcoming_discounts,
    insert_discount_version_query,
)
from data.structure.deactivation_combination import COMBINATION_COLUMNS as combination
from utils.log_error import logger
from repository.discount.write_lock import discount_write_lock


PRICE_DB = os.getenv("DB_P_NAME")
DISCOUNT_DB = os.getenv("DB_D_NAME")


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

                expired = [a for a in active_rows if a["ending_date"] < now]

                # still a valid active price -> leave the new one inactive
                if len(expired) < len(active_rows):
                    continue

                if expired:
                    sql_query, params = deactivate_price_by_ids_query([a["id"] for a in expired])
                    cursor.execute(sql_query, params)

                sql_query, params = activate_price_by_id_query(row["id"])
                cursor.execute(sql_query, params)

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



def _bump_discount_version(cursor, ids):
    """Create one new DISCOUNT_VERSION and stamp it on every changed discount."""
    ids = sorted(set(ids))
    if not ids:
        return None

    version_sql, version_params = insert_discount_version_query({
        "id": None,
        "file_name": "scheduler",
        "record_count": len(ids),
    })
    cursor.execute(version_sql, version_params)
    new_version = cursor.lastrowid

    placeholders = ", ".join(["%s"] * len(ids))
    cursor.execute(
        f"UPDATE DISCOUNT_TABLE SET version_id = %s WHERE id IN ({placeholders})",
        (new_version, *ids),
    )
    logger.info("Discount version %s stamped on %s row(s)", new_version, len(ids))
    return new_version


def check_pending_activation_discount():
    con = None
    try:
        con = get_db_connection(DISCOUNT_DB)
        with con.cursor() as cursor:
            with discount_write_lock(cursor):
                now = datetime.now()
                changed = set()

                # 1. Expired: active, end date has passed
                cursor.execute(
                    """
                    SELECT id FROM DISCOUNT_TABLE
                    WHERE active = 1
                      AND ending_date IS NOT NULL
                      AND ending_date < %s
                    """,
                    (now,),
                )
                expired_ids = [r["id"] for r in cursor.fetchall()]
                if expired_ids:
                    sql, params = deactivate_discount_by_ids_query(expired_ids)
                    cursor.execute(sql, params)
                    changed.update(expired_ids)
                    logger.info("Deactivated %s expired discount(s)", len(expired_ids))

                # 2. Upcoming: active, but start date is still in the future
                cursor.execute(
                    """
                    SELECT id FROM DISCOUNT_TABLE
                    WHERE active = 1
                      AND starting_date IS NOT NULL
                      AND starting_date > %s
                    """,
                    (now,),
                )
                upcoming_ids = [r["id"] for r in cursor.fetchall()]
                if upcoming_ids:
                    sql, params = deactivate_discount_by_ids_query(upcoming_ids)
                    cursor.execute(sql, params)
                    changed.update(upcoming_ids)
                    logger.info("Deactivated %s not-yet-started discount(s)", len(upcoming_ids))

                # 3. Pending: inactive, and the window is open now
                cursor.execute(get_pending_discount_activation_query(), (now, now))
                rows = cursor.fetchall()
                logger.info("Pending activation: %s discount(s)", len(rows))

                # 4. Latest uploaded first, so it wins within the same combination
                def still_valid(a):
                    return not (a["ending_date"] and a["ending_date"] < now)

                for row in sorted(rows, key=lambda r: r["id"], reverse=True):
                    sql_query, params = get_active_same_combination_discount_query(row, combination)
                    cursor.execute(sql_query, params)
                    active_rows = cursor.fetchall()

                    # A newer valid discount already holds this combination -> skip
                    if any(a["id"] > row["id"] and still_valid(a) for a in active_rows):
                        continue

                    # Older or expired rows for this combination go inactive
                    old_ids = [a["id"] for a in active_rows]
                    if old_ids:
                        sql, params = deactivate_discount_by_ids_query(old_ids)
                        cursor.execute(sql, params)
                        changed.update(old_ids)

                    sql, params = activate_discount_by_id_query(row["id"])
                    cursor.execute(sql, params)
                    changed.add(row["id"])

                # 5. One new version for everything this pass changed
                _bump_discount_version(cursor, changed)

                con.commit()   # commit while the lock is still held

        return rows

    except Exception:
        if con:
            con.rollback()
        logger.exception("Failed to check pending activation (discount)")
        return []

    finally:
        if con:
            con.close()




def run_scheduler(interval=10):
    while True:
        start = time.monotonic()
        check_pending_activation()
        check_pending_activation_discount()
        time.sleep(max(0, interval - (time.monotonic() - start)))