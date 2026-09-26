from datetime import datetime

def converter(value):
    if not value:
        return None
    if isinstance(value, datetime):
        return value.strftime("%Y-%m-%d %H:%M:%S")
    value = value.strip()
    formats = [
        "%Y-%m-%d %H:%M:%S.%f",  # 2026-09-26 15:35:24.168619
        "%Y-%m-%d %H:%M:%S",     # 2026-09-26 15:35:24
        "%Y-%m-%d %H:%M",        # 2026-09-26 15:35
        "%m/%d/%Y %H:%M:%S",
        "%m/%d/%Y %H:%M",
        "%Y-%m-%d",
        "%m/%d/%Y",
    ]
    for date_format in formats:
        try:
            date_value = datetime.strptime(value, date_format)

            return date_value.strftime(
                "%Y-%m-%d %H:%M:%S"
            )
        except ValueError:
            continue
    raise ValueError(
        f"Invalid datetime format: {value}"
    )

def convert_datetime(data):
    if not data:
        return data
    try:
        data["starting_date"] = converter(
            data.get("starting_date")
        )
        data["ending_date"] = converter(
            data.get("ending_date")
        )
        return data
    except Exception as e:
        return {
            "status" : "error",
            "message" : "Faild to convert datetime : {e}" 
        }