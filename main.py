from flask import Flask
from api import fetch_all_prices, create_price, update_price_data, filter_price_data, create_single_price, get_prices
from discount_api import fetch_all_discounts, create_discount, create_single_discount, update_discount_data, filter_discount_data, get_discounts
from upload_csv import upload_csv, index
# from scheduler import scheduler

app = Flask(__name__)

@app.get("/")
def index_call():
    return index()

@app.post("/api/items/upload")
def upload_csv_call():
    return upload_csv()

@app.post("/api/items/create_singel_item_price")
def add_single_price():
    return create_single_price()

@app.route('/api/items/fetch_all_item_prices', methods=['POST'])
def main_function():
    prices = fetch_all_prices()
    return prices

@app.route('/api/items/create_csv_item_prices', methods=['POST'])
def main_create_price():
    return create_price()

@app.route('/api/items/update_item_prices/<int:price_id>',methods=['PUT'])
def main_update_price(price_id):
    return update_price_data(price_id)

@app.route('/api/items/filter_item_prices', methods=['GET'])
def main_filter_prices():
    return filter_price_data()

@app.route('/api/items/get_priority_item_prices')
def get_items_prices():
    return get_prices()

@app.route('/api/items/create_single_item_discount')
def create_single_discount():
    return create_single_discount()

@app.route('/api/items/create_csv_item_discount', methods=['POST'])
def create_csv_discount():
    return create_discount()

@app.route('/api/items/fetch_all_discount_prices', methods=['POST'])
def fetch_discount():
    return fetch_all_discounts()

@app.route('/api/items/filter_discount_prices', methods=['GET'])
def filter_discount():
    return filter_discount_data()

@app.route('/api/items/update_item_discounts/<int:discount_id>', methods=['PUT'])
def update_discount(discount_id):
    return update_discount_data(discount_id)

@app.route('/api/items/get_priority_item_discount')
def get_priority_discount():
    return get_discounts()

if __name__ == "__main__":
    app.run(debug=True)