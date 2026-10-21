import os
import requests
from repository.price.fetch_store_pricing_version import (
    get_latest_version_id,
    get_version_record_count,
)
from repository.price.store_price_upload import store_create_price

HO_URL = os.getenv("HO_URL")
STORE_SITE_CODE = os.getenv("STORE_SITE_CODE")


def get_latest_version():
    return int(get_latest_version_id() or 0)


def latest_update(version, skip):
    response = requests.get(
        f"{HO_URL}/api/items/prices/version/{version}",
        params={"skip": skip, "site_code": STORE_SITE_CODE},
    )
    response.raise_for_status()
    return response.json()


def replication_main():
    latest_version = get_latest_version()
    skip = get_version_record_count(latest_version) if latest_version else 0

    records = latest_update(latest_version, skip).get("data", [])
    if not records:
        return None

    return store_create_price(records)


def run_replication(app):
    with app.app_context():
        replication_main()