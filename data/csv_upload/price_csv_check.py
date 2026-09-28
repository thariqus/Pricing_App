from utils.date_converter import convert_datetime
from utils.backdate_validator import previous_date_checker


def check_price_csv_items(records, response_message):
    invalid_item_data = []
    valid_item_data = []

    message = (response_message or {}).get("message") or {}
    missing_items = set(message.get("item", {}).get("item_codes") or [])
    missing_uoms  = set(message.get("item_uoms", {}).get("item_uom") or [])

    for data in records:

        if data.get("item_no") in missing_items:
            data["reason"] = "Item Not Found"
            invalid_item_data.append(data)
            continue

        if data.get("uom") in missing_uoms:
            data["reason"] = "UOM Not Found"
            invalid_item_data.append(data)
            continue

        # ---- date / time ----
        try:
            convert_datetime(data)          # converts in place, raises on bad format
        except ValueError as e:
            data["reason"] = f"Invalid date: {e}"
            invalid_item_data.append(data)
            continue

        reason = previous_date_checker(data)


        if reason:
            data["reason"] = reason
            invalid_item_data.append(data)
            continue


        if not data.get("starting_date") or not data.get("ending_date"):
            data["reason"] = "Starting Date and Ending Date are required"
            invalid_item_data.append(data)
            continue

        # both are 'YYYY-MM-DD HH:MM:SS', so string comparison is chronological
        if data["starting_date"] > data["ending_date"]:
            data["reason"] = "Starting Date cannot be after Ending Date"
            invalid_item_data.append(data)
            continue

        data["active"] = 1
        valid_item_data.append(data)

    return valid_item_data, invalid_item_data