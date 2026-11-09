from decimal import Decimal, InvalidOperation
from data.structure.combination_rule import PRIORITY_RULES, KEY_FIELDS, REQUIRED_NUMERIC, OPTIONAL_NUMERIC

def _is_blank(value):
    if value is None:
        return True
    if isinstance(value, float) and value != value:   # NaN
        return True
    return str(value).strip().lower() in ("", "nan", "none", "null")

def _to_number(value):
    """Return Decimal, or None for empty values. Raise ValueError for garbage."""
    if value is None:
        return None
    if isinstance(value, float):
        return None if value != value else Decimal(str(value))   # NaN check
    if isinstance(value, (int, Decimal)):
        return Decimal(value)
    s = str(value).strip().replace(",", "")
    if s == "" or s.lower() in ("nan", "none", "null"):
        return None
    try:
        return Decimal(s)
    except InvalidOperation:
        raise ValueError(f"not a number: {value!r}")

def _check_priority(data):
    # 1. priority must be a whole number 1-11
    raw = data.get("priority")
    if _is_blank(raw):
        raise ValueError("priority is empty")
    try:
        num = Decimal(str(raw).strip())
    except InvalidOperation:
        raise ValueError(f"priority is not a number: {raw!r}")
    if num != num.to_integral_value() or int(num) not in PRIORITY_RULES:
        raise ValueError(f"priority must be 1 to {len(PRIORITY_RULES)}, got {raw!r}")
    priority = int(num)
    data["priority"] = priority

    # 2. item_no and uom are always required
    for field in ("item_no", "uom"):
        if _is_blank(data.get(field)):
            raise ValueError(f"{field} is required")

    # 3. key fields for this priority must be filled
    required = PRIORITY_RULES[priority]
    missing = [f for f in required if _is_blank(data.get(f))]
    if missing:
        raise ValueError(
            f"priority {priority} requires {', '.join(required)} "
            f"(missing: {', '.join(missing)})"
        )

    # 4. key fields NOT used by this priority must be empty
    extra = [f"{f}={data.get(f)!r}" for f in KEY_FIELDS
             if f not in required and not _is_blank(data.get(f))]
    if extra:
        raise ValueError(
            f"priority {priority} must not have {', '.join(extra)} "
            f"(leave these empty or use a different priority)"
        )

def _clean_record(data):
    for field in REQUIRED_NUMERIC:
        try:
            num = _to_number(data.get(field))
        except ValueError as e:
            raise ValueError(f"{field} {e}")
        if num is None:
            raise ValueError(f"{field} is empty")
        data[field] = num
    for field in OPTIONAL_NUMERIC:
        if field in data:
            try:
                data[field] = _to_number(data[field])
            except ValueError as e:
                raise ValueError(f"{field} {e}")

    _check_priority(data)