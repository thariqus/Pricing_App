import csv
from data.structure.csv_field_mapping import CSV_FIELD_MAPPING
from utils.log_error import logger
from data.error_codes import SUCCESS, INTERNAL_SERVER_ERROR

def upload_csv(file):
    try:
        csv_file = (
            file.stream
            .read()
            .decode("utf-8-sig")
            .splitlines()
        )
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
        logger.info(
            "CSV processed successfully. %s records found",
            len(records)
        )
        return ({"records" : records, "file" : file}, {"error" : False, "error_code" : SUCCESS})
    except UnicodeDecodeError:
        logger.exception("CSV file encoding is invalid")
        return ("", {"error" : True, "error_code" : INTERNAL_SERVER_ERROR})
    except csv.Error:
        logger.exception("Invalid CSV file format")
        return ("", {"error" : True, "error_code" : INTERNAL_SERVER_ERROR})
    except Exception:
        logger.exception("Failed to process uploaded CSV file")
        return ("", {"error" : True, "error_code" : INTERNAL_SERVER_ERROR})