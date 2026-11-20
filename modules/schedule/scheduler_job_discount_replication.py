import os
import time
from services.discount.store_discount_upload import replication_main
from utils.log_error import logger

IS_CENTRAL = os.getenv("IS_CENTRAL")


def run_discount_replication_scheduler(app, interval=60):
    if IS_CENTRAL == "1":
        logger.info("Central app, replication scheduler not started")
        return

    while True:
        start = time.monotonic()
        try:
            with app.app_context():
                result = replication_main()
            logger.info("Replication run complete: %s", result)
        except Exception:
            logger.exception("Price replication scheduler failed")
        time.sleep(max(0, interval - (time.monotonic() - start)))