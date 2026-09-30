import requests
from configration.integration_ip import SITE_2113


def store_to_ho_data(site):
    try:
        if site == "2113":
            site_url = SITE_2113['ip']

        elif site == "2114":
            site_url = SITE_2113['ip']

        else:
            return {
                "status": "error",
                "message": f"Invalid site: {site}"
            }

        response = requests.post(
            f"{site_url}/api/items/fetch_all_item_prices",
            timeout=10
        )
        response_data = response.json()
        return response_data['data']

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