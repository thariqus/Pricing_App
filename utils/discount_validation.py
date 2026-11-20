from datetime import datetime, date
from decimal import Decimal, InvalidOperation

# Same access sequence as the page. Keys use the discount table column names.
PRIORITY_RULES = {
    1:  ("distribution_channel_code", "customer", "location_code"),
    2:  ("distribution_channel_code", "customer_grp", "location_code"),
    3:  ("distribution_channel_code", "customer"),
    4:  ("distribution_channel_code", "customer_grp"),
    5:  ("customer_grp",),
    6:  ("customer_hierarchy", "location_code"),
    7:  ("customer_hierarchy",),
    8:  ("distribution_channel_code", "location_code", "transportation_zone_code"),
    9:  ("distribution_channel_code", "location_code"),
    10: ("distribution_channel_code",),
    11: (),
}

KEY_FIELDS = (
    "customer",
    "customer_grp",
    "customer_hierarchy",
    "distribution_channel_code",
    "location_code",
    "transportation_zone_code",
)

DATE_FORMATS = (
    "%Y-%m-%d", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M",
    "%d-%m-%Y", "%d-%m-%Y %H:%M:%S",
    "%d/%m/%Y", "%d/%m/%Y %H:%M:%S",
)


def _blank(value):
    if value is None:
        return True
    return str(value).strip().lower() in ("", "nan", "none", "null")


def _to_decimal(value, field, errors, required=False, minimum=None):
    if _blank(value):
        if required:
            errors.append(f"{field} is required")
        return None
    try:
        num = Decimal(str(value).strip().replace(",", ""))
    except InvalidOperation:
        errors.append(f"{field} must be a number, got '{value}'")
        return None
    if minimum is not None and num < minimum:
        errors.append(f"{field} must be {minimum} or more, got {value}")
    return num


def _to_int(value, field, errors, required=False):
    num = _to_decimal(value, field, errors, required=required)
    if num is None:
        return None
    if num != num.to_integral_value():
        errors.append(f"{field} must be a whole number, got '{value}'")
        return None
    return int(num)


def _to_date(value, field, errors):
    if _blank(value):
        errors.append(f"{field} is required")
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    text = str(value).strip()
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            continue
    errors.append(f"{field} is not a valid date (use YYYY-MM-DD), got '{value}'")
    return None


def validate_discount_record(data):
    """
    Checks one record and converts its values in place.
    Returns a list of error messages. An empty list means the record is valid.
    """
    errors = []

    # Required text fields
    for field in ("item_no", "uom"):
        if _blank(data.get(field)):
            errors.append(f"{field} is required")

    # Priority and the key fields it needs
    priority = _to_int(data.get("priority"), "priority", errors, required=True)
    if priority is not None:
        if priority not in PRIORITY_RULES:
            errors.append(
                f"priority must be between 1 and {len(PRIORITY_RULES)}, got {priority}"
            )
        else:
            data["priority"] = priority
            required_keys = PRIORITY_RULES[priority]
            missing = [f for f in required_keys if _blank(data.get(f))]
            if missing:
                errors.append(
                    f"priority {priority} requires {', '.join(required_keys)} "
                    f"(missing: {', '.join(missing)})"
                )
            not_allowed = [
                f for f in KEY_FIELDS
                if f not in required_keys and not _blank(data.get(f))
            ]
            if not_allowed:
                errors.append(
                    f"priority {priority} must leave these empty: {', '.join(not_allowed)}"
                )

    # Prices and limits
    price = _to_decimal(data.get("sales_price"), "sales_price", errors,
                        required=True, minimum=Decimal("0"))
    if price is not None:
        data["sales_price"] = float(price)

    lower = _to_decimal(data.get("lower_limit"), "lower_limit", errors, minimum=Decimal("0"))
    upper = _to_decimal(data.get("upper_limit"), "upper_limit", errors, minimum=Decimal("0"))
    if lower is not None and upper is not None and lower > upper:
        errors.append(f"lower_limit ({lower}) cannot be greater than upper_limit ({upper})")
    data["lower_limit"] = float(lower) if lower is not None else None
    data["upper_limit"] = float(upper) if upper is not None else None

    min_qty = _to_int(data.get("minimum_quantity"), "minimum_quantity", errors)
    if min_qty is not None and min_qty < 0:
        errors.append("minimum_quantity cannot be negative")
    data["minimum_quantity"] = min_qty

    # Dates
    start = _to_date(data.get("starting_date"), "starting_date", errors)
    end = _to_date(data.get("ending_date"), "ending_date", errors)
    if start and end and end < start:
        errors.append(f"ending_date ({end}) cannot be before starting_date ({start})")
    data["starting_date"] = start
    data["ending_date"] = end

    # Active defaults to 1 when the CSV leaves it blank
    if _blank(data.get("active")):
        data["active"] = 1

    return errors


def validate_discount_rows(records, first_row_number=2):
    """
    Validates every record and detects duplicates inside the file.
    Row numbers assume the CSV header is line 1.
    Returns (valid_records, invalid_rows).
    """
    valid, invalid = [], []
    seen = {}

    for index, data in enumerate(records):
        row_number = index + first_row_number
        errors = validate_discount_record(data)

        if not errors:
            key = (
                data.get("item_no"), data.get("uom"), data.get("priority"),
                *(data.get(f) for f in KEY_FIELDS),
                data.get("starting_date"),
            )
            if key in seen:
                errors.append(f"duplicate of row {seen[key]}")
            else:
                seen[key] = row_number

        if errors:
            invalid.append({
                "row": row_number,
                "item_no": data.get("item_no"),
                "uom": data.get("uom"),
                "errors": errors,
            })
        else:
            valid.append(data)

    return valid, invalid