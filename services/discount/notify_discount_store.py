import os
import threading

from flask import jsonify, current_app

from services.discount.store_discount_upload import run_replication
from utils.log_error import logger

IS_CENTRAL = os.getenv("IS_CENTRAL")


def notify_discount_store():
    if IS_CENTRAL == "1":
        logger.info("Central (HO) server, skipping discount store sync")
        return jsonify({
            "status": "skipped",
            "message": "HO does not sync discounts from itself"
        }), 200

    app = current_app._get_current_object()
    thread = threading.Thread(target=run_replication, args=(app,), daemon=True)
    thread.start()

    return jsonify({"status": "Success"}), 200
