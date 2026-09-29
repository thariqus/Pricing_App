from flask import request
from services.price.ho_price_upload import ho_create_price

def ho_to_store_csv():
    data = request.get_json()
    response = ho_create_price(data, file=None, invalid_data=None)
    return response