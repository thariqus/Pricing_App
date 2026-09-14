from flask import Flask
from api import fetch_all_prices, create_price, update_price_data, filter_price_data

app = Flask(__name__)


@app.route('/api/fetch_all_prices')
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

if __name__ == "__main__":
    app.run(debug=True)