from decimal import Decimal, InvalidOperation

# Key fields as they appear in the parsed CSV record
KEY_FIELDS = (
    "customer_no",
    "customer_group",
    "customer_hierarchy",
    "distribution_channel_code",
    "location_code",
    "transportation_zone_code",
)

# Access sequence: priority -> key fields that must be filled (item_no + uom always required)
PRIORITY_RULES = {
    1:  ("distribution_channel_code", "customer_no", "location_code"),
    2:  ("distribution_channel_code", "customer_group", "location_code"),
    3:  ("distribution_channel_code", "customer_no"),
    4:  ("distribution_channel_code", "customer_group"),
    5:  ("customer_group",),
    6:  ("customer_hierarchy", "location_code"),
    7:  ("customer_hierarchy",),
    8:  ("distribution_channel_code", "location_code", "transportation_zone_code"),
    9:  ("distribution_channel_code", "location_code"),
    10: ("distribution_channel_code",),
    11: (),
}


def _is_blank(value):
    if value is None:
        return True
    if isinstance(value, float) and value != value:   # NaN
        return True
    return str(value).strip().lower() in ("", "nan", "none", "null")


def priority_error(data):
    """Return a reason string if the priority/key fields are invalid, else None.
    On success, normalizes data['priority'] to an int."""

    raw = data.get("priority")
    if _is_blank(raw):
        return "Priority is empty"

    try:
        num = Decimal(str(raw).strip())
    except InvalidOperation:
        return f"Priority is not a number: {raw}"

    if num != num.to_integral_value() or int(num) not in PRIORITY_RULES:
        return f"Priority must be 1 to {len(PRIORITY_RULES)}, got {raw}"

    priority = int(num)

    for field in ("item_no", "uom"):
        if _is_blank(data.get(field)):
            return f"{field} is required"

    required = PRIORITY_RULES[priority]
    missing = [f for f in required if _is_blank(data.get(f))]
    if missing:
        return (f"Priority {priority} requires {', '.join(required)} "
                f"(missing: {', '.join(missing)})")

    extra = [f"{f}={data.get(f)}" for f in KEY_FIELDS
             if f not in required and not _is_blank(data.get(f))]
    if extra:
        return (f"Priority {priority} must not have {', '.join(extra)} "
                f"(leave these empty or use a different priority)")

    data["priority"] = priority
    return None