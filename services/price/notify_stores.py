import threading
import requests
from concurrent.futures import ThreadPoolExecutor
from utils.log_error import logger
import os
from repository.price.fetch_store_pricing_version import get_latest_version_id
from repository.price.store_price_upload import insert_store_prices



# e.g. STORE_URLS=http://localhost:5001/api/prices,http://localhost:5002/api/prices
STORE_URLS = [u.strip().rstrip("/") for u in os.getenv("STORE_URLS", "").split(",") if u.strip()]



HO_URL = "http://localhost:5000"

IS_CENTRAL = os.getenv("IS_CENTRAL")






def _fetch_and_insert(url, next_version):
    try:
        response = requests.get(url, timeout=(3, 120))
        response.raise_for_status()
        rows = response.json().get("data", [])
        logger.info("Fetched %s price(s) from %s", len(rows), url)
    except requests.RequestException as e:
        logger.error("Fetch failed for %s: %s", url, e)
        return

    if not rows:
        logger.info("No new prices from version %s", next_version)
        return

    insert_store_prices(rows)



def ping_store(base_url=HO_URL):
    if IS_CENTRAL == "1":
        logger.info("Central (HO) server, skipping store sync")
        return {"status": "skipped", "message": "HO does not sync from itself"}

    latest = get_latest_version_id()
    next_version = (latest or 0) + 1   # fetch only versions the store doesn't have yet

    url = f"{base_url}/api/prices/version/{next_version}"
    threading.Thread(target=_fetch_and_insert, args=(url, next_version), daemon=True).start()

    logger.info("Ping received, syncing from version %s in background", next_version)
    return {"status": "received", "version_id": next_version, "url": url}