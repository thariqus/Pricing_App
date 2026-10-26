import requests
from configration.integration_ip import SITE_2113
from repository.price.fetch_price import fetch_all_prices
from repository.price.get_replication_version import get_replication_version_data
from repository.price.get_ho_version_count import get_ho_version_count

import os

STORE_URL = os.getenv("STORE_1_URL")

def store_to_ho_data(site):
    try:
        if site == "2113":
            site_url = SITE_2113['ip']

        else:
            return {
                "status": "error",
                "message": f"Invalid site: {site}"
            }

        version = get_replication_version_data(site)['replicated_version']

        response = requests.get(
            f"{STORE_URL}/api/items/get_repliaction_data/{version}",
            timeout=10
        )
        # response data
        response_data = response.json()['data']

        # remove duplication
        store_counts = list({
            row['version_id']: {
                "version_id": row['version_id'],
                "version_count": row['version_count']
            }
            for row in response_data
        }.values())

        final_version = 0

        for count in store_counts:
            ho_data = get_ho_version_count(count['version_id'], site)
            if ho_data[0]["version_count"] == count['version_count']:
                final_version = count['version_id']

        ho_datas = fetch_all_prices()
        ho_data_json = ho_datas.get_json()['data']

        filtered_data = [
            {**row, 'status': 'Failed'}
            for row in ho_data_json
            if row['version_id'] > final_version
        ]
        return filtered_data

    except requests.exceptions.Timeout:
        return {
            "status": "error",
            "message": f"Request timeout for site {site}"
        }

    except requests.exceptions.RequestException as e:
        return {
            "status": "error",
            "message": f"Request failed for site {site}",
            "error": str(e)
        }

    except ValueError:
        return {
            "status": "error",
            "message": f"Invalid JSON response from site {site}"
        }

    except Exception as e:
        return {
            "status": "error",
            "message": "Something went wrong",
            "error": str(e)
        }