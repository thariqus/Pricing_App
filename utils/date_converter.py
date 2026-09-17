from datetime import datetime

def convert_datetime(value):
    if not value:
        return None
    value = value.strip()
    formats = [
        "%m/%d/%Y %H:%M",
        "%m/%d/%Y %H:%M:%S",
        "%m/%d/%Y",
    ]
    for date_format in formats:
        try:
            date_value = datetime.strptime(value, date_format)
            return date_value.strftime("%Y-%m-%d %H:%M:%S")
        except ValueError:
            continue
    raise ValueError(f"Invalid datetime format: {value}")