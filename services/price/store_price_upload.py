import requests
from repository.price.fetch_store_pricing_version import get_latest_version_id
from services.price.ho_price_upload import ho_create_price
import os

HO_URL = os.getenv("HO_URL")

def get_latest_version():
    latest = get_latest_version_id()
    next_version = int(latest or 0)
    return next_version

def latest_update(version):
    response = requests.get(
        f"{HO_URL}/api/items/prices/version/{version}"
    )
    return response.json()

def replication_main():
    latest_version = get_latest_version()
    get_datas = latest_update(latest_version)
    response = ho_create_price(get_datas["data"], file=None, invalid_data=None)
    return response

def run_replication(app):
    with app.app_context():
        replication_main()