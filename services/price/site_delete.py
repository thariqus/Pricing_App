
from repository.price.delete_one_site import delete_one_site

def site_delete(site_id):
    if not site_id:
        return {
            "status": "error",
            "message": "Id is missing"
        }
    return delete_one_site(site_id)