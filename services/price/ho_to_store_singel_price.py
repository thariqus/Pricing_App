from flask import request
from repository.price.create_single_price import create_single_price

def ho_to_store_single_price():
    data = request.get_json()
    return create_single_price(data)