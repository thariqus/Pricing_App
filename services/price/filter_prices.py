from flask import request
from repository.price.filter_price_data import filter_price_data

def filter_items_prices():
    data = request.get_json()
    return filter_price_data(data)