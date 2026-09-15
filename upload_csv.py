from flask import render_template, request, jsonify
import csv
from api import create_price
 
def index():
    return render_template("index.html")
 
CSV_FIELD_MAPPING = {
    "Condition Type": "condition_type",
    "Item No": "item_no",
    "Customer No": "customer_no",
    "Customer Group": "customer_group",
    "Customer Hierarchy": "customer_hierarchy",
    "Distribution Channel Code": "distribution_channel_code",
    "Location Code": "location_code",
    "Priority": "priority",
    "Sales Division Code": "sales_division_code",
    "Sales Organization Code": "sales_organization_code",
    "Currency": "currency",
    "Sales Price": "sales_price",
    "Unit of Measure Code": "uom",
    "Minimum Quantity": "minimum_quantity",
    "Starting Date": "starting_date",
    "Ending Date": "ending_date",
    "Change Type": "change_type",
    "Lower Limit": "lower_limit",
    "Upper Limit": "upper_limit",
    "MAP": "map",
    "Updated From SAP": "updated_from_sap",
    "Offer Article": "offer_article",
    "Price with TAX": "price_with_tax",
    "Tax Percent": "tax_percent",
    "Transportation Zone Code": "transportation_zone_code",
}
 
 
def upload_csv():
    file = request.files.get("file")
    if not file:
        return render_template(
            "index.html",
            message="No file selected",
            message_type="error"
        )
    csv_file = file.stream.read().decode("utf-8-sig").splitlines()
    reader = csv.DictReader(csv_file)
    records = []
    for row_number, row in enumerate(reader, start=2):
        data = {}
        for csv_field, db_field in CSV_FIELD_MAPPING.items():
            value = row.get(csv_field)
            if value is None or value.strip() == "":
                value = None
            else:
                value = value.strip()
            data[db_field] = value
        records.append(data)
    return create_price(records)