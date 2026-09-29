import os
from zoneinfo import ZoneInfo

BUSINESS_TZ = ZoneInfo(os.getenv("BUSINESS_TZ", "Asia/Kolkata"))