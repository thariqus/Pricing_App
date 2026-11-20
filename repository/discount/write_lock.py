from contextlib import contextmanager

LOCK_NAME = "discount_write"


@contextmanager
def discount_write_lock(cursor, timeout=30):
    """Serialize discount writes across requests and the scheduler."""
    cursor.execute("SELECT GET_LOCK(%s, %s) AS got", (LOCK_NAME, timeout))
    row = cursor.fetchone()
    got = row["got"] if isinstance(row, dict) else row[0]
    if got != 1:
        raise RuntimeError("Discount write lock busy, try again")
    try:
        yield
    finally:
        cursor.execute("SELECT RELEASE_LOCK(%s)", (LOCK_NAME,))
        cursor.fetchall()