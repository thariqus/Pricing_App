import os
import time
from datetime import datetime, timedelta, date
from repository.price.exp_log_message import exp_log_message
from repository.price.get_expired_logs import get_expired_logs
from repository.price.remove_exp_logs import remove_exp_logs
from repository.price.per_delete_log_message import per_delete_log_message
from repository.price.get_expired_prices import get_expired_prices
from repository.price.price_item_expired import price_item_expired
from repository.price.remove_exp_price_items import remove_exp_price_items
from repository.price.per_delete_price_items import per_delete_price_items

from utils.log_error import logger

IS_CENTRAL = os.getenv("IS_CENTRAL")


def run_daily_scheduler(app):
    while True:
        try:
            now = datetime.now()

            # Calculate next midnight
            next_run = (now + timedelta(days=1)).replace(hour=0,minute=0,second=0,microsecond=0)

            sleep_seconds = (next_run - now).total_seconds()

            time.sleep(sleep_seconds)

            today = date.today()
            filter_date_30 = today - timedelta(days=30)
            filter_date_60 = today - timedelta(days=60)

            with app.app_context():
                expired_logs_message = get_expired_logs(filter_date_30)[0]
                if expired_logs_message:
                    exp_log_result, exp_log_result_error = exp_log_message(expired_logs_message)
                    if not exp_log_result_error['error']:
                        logger.info("Successfully moved %s log messages", exp_log_result)
                        remove_exp_log_message, remove_exp_log_message_error = remove_exp_logs(filter_date_30, len(expired_logs_message))
                        if not remove_exp_log_message_error['error']:
                            logger.info("Successfully deleted %s log messages", remove_exp_log_message)

                expired_prices = get_expired_prices(filter_date_30)[0]
                if expired_prices:
                    exp_price, exp_price_error = price_item_expired(expired_prices)
                    if not exp_price_error['error']:
                        logger.info("Successfully moved %s price items", exp_price)
                        remove_exp_price, remove_exp_price_error = remove_exp_price_items(filter_date_30, len(expired_prices))
                        if not remove_exp_price_error['error']:
                            logger.info("Successfully deleted %s price items", remove_exp_price)

                per_delete_logs, per_delete_logs_error = per_delete_log_message((filter_date_60))
                if not per_delete_logs_error['error']:
                    logger.info("Successfully deleted %s expired log messages from database", per_delete_logs)

                per_delete_prices, per_delete_prices_error = per_delete_price_items(filter_date_60)
                if not per_delete_prices_error['error']:
                    logger.info("Successfully deleted %s expired price items from database", per_delete_prices)

            logger.info("Daily scheduler completed")

        except Exception:
            logger.exception("Daily scheduler failed")