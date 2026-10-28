from flask import jsonify
import requests
from configration.integration_ip import SITE_2113, HEAD_OFFICE
from repository.price.get_all_site_data import get_all_site_data

def check_site(site):
    try:
        response = requests.post(
            f"{site['ip']}/api/items/fetch_all_item_prices",
            timeout=10
        )
        if response.ok:
            site["status"] = "connected"
        else:
            site["status"] = "disconnected"

    except requests.exceptions.ConnectionError as e:
        site["status"] = "disconnected"

    except requests.exceptions.Timeout as e:
        site["status"] = "disconnected"

    except requests.exceptions.RequestException as e:
        site["status"] = "disconnected"

    return site
    

def ho_to_store_integration():
    SITES = []
    sites_data = get_all_site_data()['data']
    for sites in sites_data:
        SITES.append(check_site({"ip" : sites['site_ip'], "code" : sites['site_location']}))

    return jsonify({
        "status": "success",
        "sites": SITES,
        "head" : HEAD_OFFICE
    })