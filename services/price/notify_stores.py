from flask import jsonify, current_app
import threading
import os
from services.price.store_price_upload import run_replication
from utils.log_error import logger

IS_CENTRAL = os.getenv("IS_CENTRAL")

def notify_store():
    if IS_CENTRAL == "1":
        logger.info("Central (HO) server, skipping store sync")
        return {"status": "skipped", "message": "HO does not sync from itself"}
    app = current_app._get_current_object()

    thread = threading.Thread(
        target=run_replication,
        args=(app,),
        daemon=True
    )
    thread.start()

    return jsonify({
        "status" : "Success"
    }, 200)
