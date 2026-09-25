from flask import Flask, render_template
from services.price.create_single_price import create_single_item_price
from services.price.fetch_all_price import fetch_all_items_prices
from services.price.update_price import update_item_price
from services.price.ho_price_upload import ho_price_upload
from services.price.filter_prices import filter_items_prices
from services.price.get_priority import get_items_price_priority
from discount_api import fetch_all_discounts, create_single_discount, update_discount_data, filter_discount_data, get_discounts
from data.csv_upload.discount_csv_upload import upload_discount_csv
from datetime import datetime, date
from flask.json.provider import DefaultJSONProvider

app = Flask(__name__)

 
class CustomJSONProvider(DefaultJSONProvider):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.strftime("%Y-%m-%d %H:%M:%S")
        if isinstance(obj, date):
            return obj.strftime("%Y-%m-%d")
        return super().default(obj)
 
 
app.json = CustomJSONProvider(app)

#pages
@app.get("/")
def index_call():
    return render_template("index.html")

@app.get("/integration")
def integration():
    return render_template("integration.html")

@app.get("/settings")
def settings():
    settings = []
    return render_template("settings.html", settings=settings)

@app.get("/site-details")
def site_details():
    return render_template("site_detail.html")

#functions
@app.post("/api/items/create_singel_item_price")
def add_single_price():
    return create_single_item_price()

@app.route('/api/items/fetch_all_item_prices', methods=['POST'])
def main_function():
    return fetch_all_items_prices()

@app.route('/api/items/update_item_prices/',methods=['PUT'])
def main_update_price():
    return update_item_price()

@app.route('/api/items/filter_item_prices', methods=['POST'])
def main_filter_prices():
    return filter_items_prices()

@app.route('/api/items/get_priority_item_prices')
def get_items_prices():
    return get_items_price_priority()

@app.route('/api/items/create_single_item_discount')
def create_single_discount():
    return create_single_discount()

@app.route('/api/items/create_csv_item_discount', methods=['POST'])
def create_csv_discount():
    return upload_discount_csv()

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

@app.route("/api/items/central_app", methods=['POST'])
def central_app():
    return ho_price_upload()