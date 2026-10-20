import time
from services.price.store_price_upload import run_replication
from flask import current_app
from utils.log_error import logger


def run_replication_scheduler(interval=10):
    while True:
        start = time.monotonic()

        try:
            app = current_app._get_current_object()
            run_replication(app)
            logger.info("Price replication scheduler executed successfully")

        except Exception:
            logger.exception("Price replication scheduler failed")

        elapsed = time.monotonic() - start
        time.sleep(max(0, interval - elapsed))