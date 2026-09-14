import csv, io
from datetime import datetime
from flask import (Flask, render_template, request,
                   redirect, url_for, flash)
 
app = Flask(__name__)
app.secret_key = "change-me"
app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024
 
RECORDS = []          # in-memory store; swap for Mongo later
 
# CSV header -> mongo field
FIELD_MAP = {
    "Condition Type":            "condition_type",
    "Item No":                   "item_no",
    "Customer No":               "customer_no",
    "Customer Group":            "customer_group",
    "Customer Hierarchy":        "customer_hierarchy",
    "Distribution Channel Code": "distribution_channel_code",
    "Location Code":             "location_code",
    "Priority":                  "priority",
    "Sales Division Code":       "sales_division_code",
    "Sales Organization Code":   "sales_organization_code",
    "Currency":                  "currency",
    "Sales Price":               "sales_price",
    "Unit of Measure Code":      "uom",
    "Minimum Quantity":          "minimum_quantity",
    "Starting Date":             "starting_date",
    "Ending Date":               "ending_date",
    "Change Type":               "change_type",
    "Lower Limit":               "lower_limit",
    "Upper Limit":               "upper_limit",
    "MAP":                       "map",
    "Updated From SAP":          "updated_from_sap",
    "Offer Article":             "offer_article",
    "Price with TAX":            "price_with_tax",
    "Tax Percent":               "tax_percent",
    "Transportation Zone Code":  "transportation_zone_code",
}
 
REQUIRED = ["Condition Type", "Item No", "Sales Price",
            "Unit of Measure Code", "Starting Date", "Ending Date"]
 
FLOAT_FIELDS = {"sales_price", "lower_limit", "upper_limit",
                "minimum_quantity", "tax_percent"}
INT_FIELDS   = {"priority"}
DATE_FIELDS  = {"starting_date", "ending_date"}
BOOL_FIELDS  = {"map", "updated_from_sap", "offer_article", "price_with_tax"}
 
DATE_FORMATS = ("%m/%d/%Y %H:%M", "%m/%d/%Y", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d")
 
 
def parse_date(value):
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue
    raise ValueError(f"unrecognised date {value!r}")
 
 
def parse_bool(value):
    return value.strip().lower() in {"1", "true", "yes", "y", "x"}
 
 
def build_doc(row):
    doc = {}
    for header, field in FIELD_MAP.items():
        raw = (row.get(header) or "").strip()
 
        if field in BOOL_FIELDS:
            doc[field] = parse_bool(raw)
            continue
        if raw == "":
            doc[field] = None
            continue
        if field in DATE_FIELDS:
            doc[field] = parse_date(raw)
        elif field in FLOAT_FIELDS:
            doc[field] = float(raw)
        elif field in INT_FIELDS:
            doc[field] = int(float(raw))
        else:
            doc[field] = raw
 
    if doc["starting_date"] and doc["ending_date"] \
            and doc["ending_date"] < doc["starting_date"]:
        raise ValueError("ending date is before starting date")
 
    return doc
 
 

def index():
    return render_template("index.html", title="Price Records", items=RECORDS)
 
 
def upload_csv():
    file = request.files.get("file")
    if not file or not file.filename:
        flash("No file selected", "error")
        return redirect(url_for("index"))
    if not file.filename.lower().endswith(".csv"):
        flash("Please upload a .csv file", "error")
        return redirect(url_for("index"))
 
    stream = io.StringIO(file.stream.read().decode("utf-8-sig"), newline=None)
    reader = csv.DictReader(stream)
 
    headers = [h.strip() for h in (reader.fieldnames or [])]
    missing = [h for h in REQUIRED if h not in headers]
    if missing:
        flash(f"Missing columns: {', '.join(missing)}", "error")
        return redirect(url_for("index"))
 
    docs, errors = [], []
    for line_no, row in enumerate(reader, start=2):
        if not any((v or "").strip() for v in row.values()):
            continue
        try:
            docs.append(build_doc(row))
        except (ValueError, TypeError) as e:
            errors.append(f"row {line_no}: {e}")
 
    RECORDS.extend(docs)
 
    msg = f"Imported {len(docs)} price records"
    if errors:
        msg += f" — skipped {len(errors)}: " + "; ".join(errors[:5])
        if len(errors) > 5:
            msg += f" (+{len(errors) - 5} more)"
    flash(msg, "success" if docs else "error")
    return redirect(url_for("index")) 