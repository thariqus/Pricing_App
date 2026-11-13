import os
import requests
from repository.discount.store_discount_upload import (
    get_store_latest_discount_version,
    get_store_discount_version_count,
    store_create_discount,
)
from utils.log_error import logger

HO_URL = os.getenv("HO_URL")
STORE_SITE_CODE = os.getenv("STORE_SITE_CODE")


def latest_update(version, skip):
    response = requests.get(
        f"{HO_URL}/api/items/discount/version/{version}",
        params={"skip": skip, "site_code": STORE_SITE_CODE},
        timeout=60,
    )
    response.raise_for_status()
    return response.json()


def replication_main():
    """Pull every HO discount this store has not received yet (filtered by site on the HO)."""
    latest_version = get_store_latest_discount_version()
    skip = get_store_discount_version_count(latest_version) if latest_version else 0

    records = latest_update(latest_version, skip).get("data", [])
    if not records:
        logger.info("Discount replication: nothing new after version %s", latest_version)
        return None

    return store_create_discount(records)


def run_replication(app):
    with app.app_context():
        replication_main()
