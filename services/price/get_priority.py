from flask import request
from repository.price.get_price_priority import get_price_priority

def get_items_price_priority():
    data = request.get_json()
    return get_price_priority(data)