from utils.date_converter import convert_datetime
from utils.backdate_validator import previous_date_checker
from utils.invalid_csv_list import reject_csv_list


def check_price_csv_items(records, response_message):
    invalid_item_data = []
    valid_item_data = []

    message = (response_message or {}).get("message") or {}

    missing_items = set(
        message.get("item", {}).get("item_codes") or []
    )

    missing_item_uoms = {
        (
            item.get("item_code"),
            item.get("uom")
        )
        for item in message.get("item_uoms", {}).get("item_uom", [])
        if item.get("item_code") and item.get("uom")
    }

    for data in records:

        raw = dict(data)

        if data.get("item_no") in missing_items:
            invalid_item_data = reject_csv_list(
                invalid_item_data,
                "Item Not Found",
                raw
            )
            continue

        item_uom = (
            data.get("item_no"),
            data.get("uom")
        )

        if item_uom in missing_item_uoms:
            invalid_item_data = reject_csv_list(
                invalid_item_data,
                "UOM Not Found",
                raw
            )
            continue
 
        # ---- date / time ----
        try:
            convert_datetime(data)          # mutates `data` only, `raw` stays original
        except ValueError as e:
            invalid_item_data = reject_csv_list(invalid_item_data, f"Invalid date: {e}", raw)
            continue
 
        reason = previous_date_checker(data)
        if reason:
            invalid_item_data = reject_csv_list(invalid_item_data, reason, raw)
            continue
 
        if not data.get("starting_date") or not data.get("ending_date"):
            invalid_item_data = reject_csv_list(invalid_item_data, "Starting Date and Ending Date are required", raw)
            continue
 
        # both are 'YYYY-MM-DD HH:MM:SS', so string comparison is chronological
        if data["starting_date"] > data["ending_date"]:
            invalid_item_data = reject_csv_list(invalid_item_data, "Starting Date cannot be after Ending Date", raw)
            continue

        
 
        data["active"] = 1
        valid_item_data.append(data)
 
    return valid_item_data, invalid_item_data