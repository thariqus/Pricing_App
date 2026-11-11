REQUIRED_NUMERIC = ("sales_price",)

PRIORITY_RULES = {
    1:  ("distribution_channel_code", "customer_no", "location_code"),
    2:  ("distribution_channel_code", "customer_group", "location_code"),
    3:  ("distribution_channel_code", "customer_no"),
    4:  ("distribution_channel_code", "customer_group"),
    5:  ("customer_group",),
    6:  ("customer_hierarchy", "location_code"),
    7:  ("customer_hierarchy",),
    8:  ("distribution_channel_code", "location_code", "transportation_zone_code"),
    9:  ("distribution_channel_code", "location_code"),
    10: ("distribution_channel_code",),
    11: (),
}

KEY_FIELDS = (
    "customer_no",
    "customer_group",
    "customer_hierarchy",
    "distribution_channel_code",
    "location_code",
    "transportation_zone_code",
)

OPTIONAL_NUMERIC = ("lower_limit", "upper_limit", "minimum_quantity")

FIELD_MAP = {
    "customer_no":               "customer",
    "customer_group":            "customer_grp",
    "customer_hierarchy":        "customer_hierarchy",
    "distribution_channel_code": "distribution_channel_code",
    "location_code":             "location_code",
    "transportation_zone_code":  "transportation_zone_code",
}