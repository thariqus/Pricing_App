from datetime import datetime
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
 
 
class ValidationError(Exception):
    def __init__(self, errors):
        self.errors = errors          # dict of {field: error message}
        super().__init__(errors)
 
 
class PriceConditionValidator:
    # Your body uses two different date formats, so we accept both
    DATE_FORMATS = ["%Y-%m-%d %H:%M:%S", "%m/%d/%Y %H:%M"]
 
    def __init__(self, data):
        self.data = data      # the raw body
        self.errors = {}      # problems found
        self.cleaned = {}     # values after checking/converting
 
    def validate(self):
 
        # ---------- required text fields ----------
        self._text("condition_type", required=True)
        self._text("item_no", required=True)
        self._text("uom",required=True)
 
        #---------- optional text fields ----------
        self._text("distribution_channel_code", required=False)
        self._text("customer_no", required=False)
        self._text("customer_group", required=False)
        self._text("customer_hierarchy", required=False)
        self._text("location_code", required=False)
        self._text("transportation_zone_code", required=False)  
 
        # Whole numbers
        self._integer("priority", required=True)
        self._integer("updated_from_sap", required=True, allowed=[0, 1])
 
        # Prices and quantities (sent as strings like "12.50")
        self._decimal("sales_price", required=True)
        self._decimal("price_with_tax", required=False)
        self._decimal("tax_percent", required=False)
        self._decimal("minimum_quantity", required=False)
        self._decimal("lower_limit", required=False)
        self._decimal("upper_limit", required=False)
 
        # Dates
        self._date("starting_date", required=True)
        self._date("ending_date", required=True)
 
        # Checks that compare two or more fields
        self._cross_checks()
 
        if self.errors:
            raise ValidationError(self.errors)
        return self.cleaned
 
    # ---------- helpers ----------
 
    def _is_empty(self, value):
        return value is None or (isinstance(value, str) and value.strip() == "")
 
    def _text(self, field, required):
        value = self.data.get(field)
        if self._is_empty(value):
            if required:
                self.errors[field] = "This field is required"
            else:
                self.cleaned[field] = ""
            return
        if not isinstance(value, str):
            self.errors[field] = "Must be text"
            return
        self.cleaned[field] = value.strip()
 
    def _integer(self, field, required, allowed=None):
        value = self.data.get(field)
        if self._is_empty(value):
            if required:
                self.errors[field] = "This field is required"
            else:
                self.cleaned[field] = None
            return
        try:
            value = int(value)
        except (ValueError, TypeError):
            self.errors[field] = "Must be a whole number"
            return
        if allowed is not None and value not in allowed:
            self.errors[field] = f"Must be one of {allowed}"
            return
        self.cleaned[field] = value
 
    def _decimal(self, field, required):
        value = self.data.get(field)
        if self._is_empty(value):
            if required:
                self.errors[field] = "This field is required"
            else:
                self.cleaned[field] = None
            return
        try:
            value = Decimal(str(value).strip())
        except InvalidOperation:
            self.errors[field] = "Must be a number"
            return
        if value < 0:
            self.errors[field] = "Cannot be negative"
            return
        self.cleaned[field] = value
 
    def _date(self, field, required):
        value = self.data.get(field)
        if self._is_empty(value):
            if required:
                self.errors[field] = "This field is required"
            else:
                self.cleaned[field] = None
            return
        if not isinstance(value, str):
            self.errors[field] = "Must be a date string"
            return
        for fmt in self.DATE_FORMATS:
            try:
                self.cleaned[field] = datetime.strptime(value.strip(), fmt)
                return
            except ValueError:
                continue
        self.errors[field] = "Invalid date. Use 'YYYY-MM-DD HH:MM:SS' or 'MM/DD/YYYY HH:MM'"
 
    def _cross_checks(self):
        c = self.cleaned
 
        # Currency should be a 3-letter code like AED
        if c.get("currency") and len(c["currency"]) != 3:
            self.errors["currency"] = "Must be a 3-letter code like AED"
 
        # Ending date must be after starting date
        if c.get("starting_date") and c.get("ending_date"):
            if c["ending_date"] <= c["starting_date"]:
                self.errors["ending_date"] = "Must be after starting_date"
 
        # Lower limit must not be bigger than upper limit
        if c.get("lower_limit") is not None and c.get("upper_limit") is not None:
            if c["lower_limit"] > c["upper_limit"]:
                self.errors["lower_limit"] = "Cannot be greater than upper_limit"
 
        # price_with_tax should equal sales_price + tax
        if (c.get("sales_price") is not None
                and c.get("tax_percent") is not None
                and c.get("price_with_tax") is not None):
            expected = c["sales_price"] * (1 + c["tax_percent"] / 100)
            expected = expected.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            if abs(expected - c["price_with_tax"]) > Decimal("0.01"):
                self.errors["price_with_tax"] = f"Expected about {expected}"
 
 
# ---------- Usage ----------
 
body = {
    "condition_type": "ZPR0",
    "item_no": "100012345",
    "uom": "EA",
    "priority": 10,
    "distribution_channel_code": "10",
    "customer_no": "",
    "customer_group": "",
    "customer_hierarchy": "",
    "location_code": "",
    "transportation_zone_code": "",
    "currency": "AED",
    "sales_price": "12.50",
    "minimum_quantity": "1",
    "lower_limit": "",
    "upper_limit": "",
    "starting_date": "2026-11-12 00:00:00",
    "ending_date": "12/30/9999 23:59",
    "map": "",
    "change_type": "",
    "updated_from_sap": 0,
    "sales_division_code": "",
    "offer_article": "",
    "price_with_tax": "13.13",
    "tax_percent": "5",
}
 
# Valid body
try:
    data = PriceConditionValidator(body).validate()
    print("Valid!", data["item_no"], data["sales_price"], data["ending_date"])
except ValidationError as e:
    print("Errors:", e.errors)
 
# Invalid body
bad_body = dict(body, sales_price="abc", starting_date="12-11-2026")
try:
    PriceConditionValidator(bad_body).validate()
except ValidationError as e:
    print("Errors:", e.errors)
 