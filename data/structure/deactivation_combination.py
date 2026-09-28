# Columns that identify a price condition. Edit here if the business rule changes.
COMBINATION_COLUMNS = {
    # DB column                : keys it may arrive under
    "condition_type":            ("condition_type",),
    "item_no":                   ("item_no",),
    "customer":                  ("customer", "customer_no"),
    "customer_grp":              ("customer_grp", "customer_group"),
    "customer_hierarchy":        ("customer_hierarchy",),
    "distribution_channel_code": ("distribution_channel_code", "distribution_channel"),
    "location_code":             ("location_code",),
    "transportation_zone_code":  ("transportation_zone_code", "zone_code"),
    "priority":                  ("priority",),
    "uom":                       ("uom",),
    "minimum_quantity":          ("minimum_quantity", "min_qty"),
}

