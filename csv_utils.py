from datetime import datetime
 
 
# CSV header -> DB column
FIELD_MAP = {
    "Active":                    "active",
    "Condition Type":            "condition_type",
    "Item No":                   "item_no",
    "Customer No":               "customer",
    "Customer Group":            "customer_grp",
    "Customer Hierarchy":        "customer_hierarchy",
    "Distribution Channel Code": "distribution_channel_code",
    "Location Code":             "location_code",
    "Priority":                  "priority",
    "Sales Division Code":       "sales_division_code",
    "Currency":                  "currency",
    "Sales Price":               "sales_price",
    "Unit of Measure Code":      "unit_of_measure",
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
 
REQUIRED = [
    "Condition Type", "Item No", "Sales Price",
    "Unit of Measure Code", "Starting Date", "Ending Date",
]
 
FLOAT_FIELDS = {
    "sales_price", "lower_limit", "upper_limit",
    "tax_percent", "price_with_tax",
}
 
INT_FIELDS = {
    "priority", "customer_grp", "customer_hierarchy",
    "distribution_channel_code", "location_code",
    "sales_division_code", "minimum_quantity",
}
 
DATE_FIELDS = {"starting_date", "ending_date"}
 
BOOL_FIELDS = {"active", "updated_from_sap", "offer_article"}
 
# ISO first — it's what the app's own CSV export produces.
DATE_FORMATS = (
    "%Y-%m-%d %H:%M:%S",
    "%Y-%m-%d",
    "%m/%d/%Y %H:%M:%S",
    "%m/%d/%Y %H:%M",
    "%m/%d/%Y",
)
 
 
def parse_number(value):
    """SAP exports use thousands separators — 1,325.00 -> 1325.0"""
    return value.replace(",", "").replace(" ", "")
 
 
def parse_date(value):
 
    for fmt in DATE_FORMATS:
        try:
            parsed = datetime.strptime(value, fmt)
            # SAP's "never expires" sentinel
            if parsed.year == 9999:
                return None
            return parsed
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
            doc[field] = float(parse_number(raw))
        elif field in INT_FIELDS:
            doc[field] = int(float(parse_number(raw)))
        else:
            doc[field] = raw
 
    if doc["starting_date"] and doc["ending_date"] \
            and doc["ending_date"] < doc["starting_date"]:
        raise ValueError("ending date is before starting date")
 
    return doc
 