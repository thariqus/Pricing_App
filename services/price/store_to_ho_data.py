import requests
from configration.integration_ip import SITE_2113
from repository.price.fetch_price import fetch_all_prices


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

        ho_datas = fetch_all_prices()
        ho_data_json = ho_datas.get_json()

        store_data_list = response_data["data"]
        ho_data_list = ho_data_json["data"]

        for ho_data in ho_data_list:

            found = False

            for store_data in store_data_list:

                if ho_data == store_data:
                    store_data["status"] = "Success"
                    found = True
                    break

            if not found:

                failed_data = ho_data.copy()
                failed_data["status"] = "Failed"

                store_data_list.append(failed_data)
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