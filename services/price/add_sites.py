from flask import request
from repository.price.add_site_details import add_site_details

def add_sites():
    data = request.get_json()
    if not data:
        return {
            "status": "error",
            "message": "Data is missing"
        }
    return add_site_details(data)