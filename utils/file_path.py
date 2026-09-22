import os
from datetime import datetime
now = datetime.now()

year = now.strftime("%Y")
month = now.strftime("%m")

upload_price_directory = os.path.join(
    "uploads",
    "prices",
    year,
    month
)

upload_discount_directory = os.path.join(
    "uploads",
    "discounts",
    year,
    month
)

os.makedirs(
    upload_price_directory,
    exist_ok=True
)

os.makedirs(
    upload_discount_directory,
    exist_ok=True
)