from apscheduler.schedulers.background import BackgroundScheduler

from api import deactive_items
import logging


# Logging configuration
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)


def check_item_exp():
    try:
        result = deactive_items()
        logger.info(
            f"Scheduler completed: {result}"
        )
    except Exception:
        logger.exception(
            "Scheduled item expiration check failed"
        )

scheduler = BackgroundScheduler()

scheduler.add_job(
    check_item_exp,
    trigger="interval",
    minutes=1
)

scheduler.start()