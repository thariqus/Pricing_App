from flask import request
from repository.price.edit_one_site import edit_one_site

def site_edit(site_id):
    data = request.get_json()
    if not site_id:
        return {
            "status": "error",
            "message": "Id is missing"
        }
    if not data:
        return {
            "status": "error",
            "message": "No valid data"
        }
    return edit_one_site(site_id, data)