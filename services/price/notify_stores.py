from flask import jsonify, current_app
import requests
from repository.price.fetch_store_pricing_version import get_latest_version_id
from services.price.ho_price_upload import ho_create_price
import threading
import os
from utils.log_error import logger

HO_URL = "http://172.16.51.68:5002"
IS_CENTRAL = os.getenv("IS_CENTRAL")

def get_latest_version():
    print("latest version id get function")
    latest = get_latest_version_id()
    next_version = int(latest or 0)
    return next_version

def latest_update(version):
    print("latest updated data call function")
    response = requests.get(
        f"{HO_URL}/api/items/prices/version/{version}"
    )
    return response.json()

def replication_main():
    print("Calling the latest version get function")
    latest_version = get_latest_version()
    print("Call the latest update get data function")
    get_datas = latest_update(latest_version)
    print("Calling create price ho function")
    response = ho_create_price(get_datas["data"], file=None, invalid_data=None)
    return response

def run_replication(app):
    print("Json response checker")
    with app.app_context():
        replication_main()

def notify_store():
    print("Checking the centeral app")
    if IS_CENTRAL == "1":
        logger.info("Central (HO) server, skipping store sync")
        return {"status": "skipped", "message": "HO does not sync from itself"}
    app = current_app._get_current_object()

    print("Calling threading function")

    thread = threading.Thread(
        target=run_replication,
        args=(app,),
        daemon=True
    )
    thread.start()

    print("Threading function completed..")
    return jsonify({
        "status" : "Success"
    }, 200)
