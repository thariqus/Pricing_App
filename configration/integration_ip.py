import os

STORE_1_URL = os.getenv("STORE_1_URL") 

HEAD_OFFICE = {"code": "HO", "name": "Head Office"}
SITE_2113 = {
        "code": "2113",
        "ip" : STORE_1_URL
    }

SITES = [
    STORE_1_URL
]