from flask import Flask, render_template, request
import requests
from services.price.create_single_price import create_single_item_price
from services.price.fetch_all_price import fetch_all_items_prices
from services.price.update_price import update_item_price
from services.price.ho_price_upload import ho_price_upload
from services.price.filter_prices import filter_items_prices
from services.price.get_priority import get_items_price_priority
from services.price.ho_to_store_csv import ho_to_store_csv
from services.price.ho_to_store_integration import ho_to_store_integration
from services.price.store_to_ho_data import store_to_ho_data
from services.price.ho_to_store_singel_price import ho_to_store_single_price
from services.price.notify_stores import notify_store
from services.price.get_logs import get_logs
from services.price.get_replication import get_replication
from services.price.add_sites import add_sites
from services.price.get_all_sites import get_all_sites
from services.price.site_delete import site_delete
from services.price.site_edit import site_edit
from discount_api import fetch_all_discounts, create_single_discount, update_discount_data, filter_discount_data, get_discounts
from data.csv_upload.discount_csv_upload import upload_discount_csv
from datetime import datetime, date
from flask.json.provider import DefaultJSONProvider

from repository.price.fetch_ho_price_records_by_version import get_prices_from_version
from flask import jsonify
from utils.auth import admin_required

import os
IS_CENTRAL = os.getenv("IS_CENTRAL")


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

@app.get("/log_message")
# @admin_required
def log_message():
    messages = get_logs()
    return render_template("log_message.html", messages=messages)

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

@app.route('/api/get_discounted_item_price', methods=['POST'])
def get_items_prices():
    return get_items_price_priority()

#discount pages

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

@app.get("/discount")
def discount():
    return render_template("discount.html")
 

@app.route("/api/items/central_app", methods=['POST'])
def central_app():
    return ho_price_upload()

#integration
@app.post("/api/items/store_csv_uploads")
def ho_store_csv_upload():
    return ho_to_store_csv()

@app.post("/api/items/store_singel_price")
def ho_to_store_price():
    return ho_to_store_single_price()

#integration pages
@app.get("/integration")
def integration():
    return render_template("integration.html")

@app.route("/api/items/integration_check")
def integration_check():
    return ho_to_store_integration()

@app.route("/api/items/get_repliaction_data/<int:version_id>")
def get_replication_data(version_id):
    return get_replication(version_id)

@app.get("/settings")
def settings():
    settings = []
    return render_template("settings.html", settings=settings, is_central=IS_CENTRAL)

@app.get("/site-details/<siteid>")
def site_details(siteid):
    items  = store_to_ho_data(siteid)
    return render_template("site_detail.html", items=items)

@app.route("/api/items/notify_stores", methods=['GET'])
def get_notification():
    return notify_store()

@app.route("/api/items/prices/version/<int:version_id>")
def prices_from_version(version_id):
    skip = request.args.get("skip", 0, type=int)
    site_code = request.args.get("site_code", type=int)
    rows = get_prices_from_version(version_id, site_code, skip)
    return jsonify({
        "status": "success",
        "version_id": version_id,
        "count": len(rows),
        "data": rows,
    }), 200

# site settings code

@app.route("/api/add_site_settings", methods=['POST'])
def add_site_settings():
    return add_sites()

@app.route("/api/get_all_sites")
def get_site_details():
    return get_all_sites()

@app.route("/api/delete_site/<int:site_id>", methods=['DELETE'])
def delete_site(site_id):
    return site_delete(site_id)

@app.route("/api/update_site/<int:site_id>", methods=['PUT'])
def edit_site(site_id):
    return site_edit(site_id)