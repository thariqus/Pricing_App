import csv
from data.structure.csv_field_mapping import CSV_FIELD_MAPPING
from utils.log_error import logger

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
        return records, file
    except UnicodeDecodeError:
        logger.exception("CSV file encoding is invalid")
        raise ValueError(
            "Invalid CSV encoding. Please upload a UTF-8 CSV file."
        )
    except csv.Error:
        logger.exception("Invalid CSV file format")
        raise ValueError(
            "Invalid CSV file format."
        )
    except Exception:
        logger.exception("Failed to process uploaded CSV file")
        raise