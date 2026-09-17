from apscheduler.schedulers.background import BackgroundScheduler
from api import deactive_price_items
from discount_api import deactive_discount_items
from utils.log_error import logger


def check_item_exp():
    try:
        result = deactive_price_items()
        logger.info(
            "Price item expiration check completed: %s",
            result
        )
    except Exception:
        logger.exception(
            "Price item expiration check failed"
        )
    try:
        discount_result = deactive_discount_items()
        logger.info(
            "Discount item expiration check completed: %s",
            discount_result
        )
    except Exception:
        logger.exception(
            "Discount item expiration check failed"
        )

scheduler = BackgroundScheduler()

scheduler.add_job(
    check_item_exp,
    trigger="interval",
    minutes=1
)

scheduler.start()