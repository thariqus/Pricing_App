from flask import render_template, request
import csv
from discount_api import create_discount
from data.structure.csv_field_mapping import CSV_FIELD_MAPPING

def upload_discount_csv():
    file = request.files.get("file")
    if not file:
        return render_template(
            "index.html",
            message="No file selected",
            message_type="error"
        )
    csv_file = file.stream.read().decode("utf-8-sig").splitlines()
    reader = csv.DictReader(csv_file)
    records = []
    for row_number, row in enumerate(reader, start=2):
        data = {}
        for csv_field, db_field in CSV_FIELD_MAPPING.items():
            value = row.get(csv_field)
            if value is None or value.strip() == "":
                value = None
            else:
                value = value.strip()
            data[db_field] = value
        records.append(data)
    return create_discount(records, file)