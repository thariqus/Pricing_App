from datetime import datetime

DB_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def previous_date_checker(data, now=None):
    """
    Check the (already converted) dates on a price record.

    Rules:
      - starting_date can't be before today (00:00 today is allowed)
      - ending_date can't be in the past
      - starting_date can't be after ending_date

    Returns None if valid, or a reason string if not.
    """
    now = now or datetime.now()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

    starting = data.get("starting_date")
    ending   = data.get("ending_date")

    if not starting or not ending:
        return "Starting Date and Ending Date are required"

    start_dt = datetime.strptime(starting, DB_DATE_FORMAT)
    end_dt   = datetime.strptime(ending, DB_DATE_FORMAT)

    if start_dt < today_start:
        return f"Starting Date {starting} is a previous date"

    if end_dt < now:
        return f"Ending Date {ending} is already in the past"

    if start_dt > end_dt:
        return "Starting Date cannot be after Ending Date"

    return None