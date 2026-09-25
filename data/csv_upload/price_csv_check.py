from flask import jsonify
from utils.date_converter import convert_datetime

def check_price_csv_items(records, response_message):
    Invalid_item_data = []
    valid_item_data = []
    items_no = response_message["message"]["item"]["item_codes"]
    uoms = response_message["message"]["item_uoms"]["item_uom"]
    for data in records:
        if data["item_no"] in items_no:
            data["reason"] = "Item Not Found"
            Invalid_item_data.append(data)
        else:
            if data["uom"] in uoms:
                data["reason"] = "UOM Not Found"
                Invalid_item_data.append(data)
            else:
                formatted_data = convert_datetime(data)
                data["active"] = 0
                valid_item_data.append(formatted_data)
    return valid_item_data, Invalid_item_data