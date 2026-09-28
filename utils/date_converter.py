import re
from datetime import datetime

DATE_FORMATS = [
    "%Y-%m-%d %H:%M:%S.%f",   # 2026-09-26 15:35:24.168619
    "%Y-%m-%d %H:%M:%S",      # 2026-09-26 15:35:24
    "%Y-%m-%d %H:%M",         # 2026-09-26 15:35
    "%Y-%m-%d",
    "%m/%d/%Y %H:%M:%S",      # 9/27/2026 18:55:00
    "%m/%d/%Y %H:%M",         # 12/30/9999 23:59
    "%m/%d/%Y %I:%M:%S %p",   # 9/27/2026 06:55:00 PM
    "%m/%d/%Y %I:%M %p",
    "%m/%d/%Y",
]

# time followed by AM/PM, capturing the hour
_AMPM_RE = re.compile(r"^(.*?(\d{1,2}):\d{2}(?::\d{2})?)\s*([AaPp][Mm])$")


def converter(value):
    """Return 'YYYY-MM-DD HH:MM:SS', None for blanks, or raise ValueError."""
    if value is None:
        return None

    if isinstance(value, datetime):
        return value.strftime("%Y-%m-%d %H:%M:%S")

    text = " ".join(str(value).split())      # trim + collapse double spaces

    if not text:
        return None

    # '18:55:00 PM': hour is already 24h, so the AM/PM suffix is meaningless
    match = _AMPM_RE.match(text)
    if match:
        base, hour, _ = match.groups()
        if int(hour) > 12 or int(hour) == 0:
            text = base

    for date_format in DATE_FORMATS:
        try:
            return datetime.strptime(text, date_format).strftime("%Y-%m-%d %H:%M:%S")
        except ValueError:
            continue

    raise ValueError(f"Invalid datetime format: {value!r}")


def convert_datetime(data):
    """Convert the date fields in place. Raises ValueError on a bad date."""
    if not data:
        return data

    data["starting_date"] = converter(data.get("starting_date"))
    data["ending_date"]   = converter(data.get("ending_date"))

    return data