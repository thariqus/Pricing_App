from flask import Flask
from api import fetch_all_prices, create_price, update_price_data, filter_price_data, create_single_price, get_prices
from upload_csv import upload_csv, index
# from scheduler import scheduler

app = Flask(__name__)

@app.get("/")
def index_call():
    return index()

@app.post("/api/items/upload")
def upload_csv_call():
    return upload_csv()

@app.post("/api/items/singel_price")
def add_single_price():
    return create_single_price()

@app.route('/api/fetch_all_prices', methods=['POST'])
def main_function():
    prices = fetch_all_prices()
    return prices

@app.route('/api/create_price', methods=['POST'])
def main_create_price():
    price = create_price()
    return price

@app.route('/api/update_price/<int:price_id>',methods=['PUT']
)
def main_update_price(price_id):
    price = update_price_data(price_id)
    return price

@app.route('/api/filter_prices', methods=['GET'])
def main_filter_prices():
    return filter_price_data()

@app.route('/api/get_item_price')
def get_items_prices():
    return get_prices()

if __name__ == "__main__":
    app.run(debug=True)