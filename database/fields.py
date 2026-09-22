#Pricing Items fields
Pricing_Table = {
    "id": {
        "type": "INT",
        "auto_increment": True,
        "primary_key": True
    },
    "active": {
        "type": "BOOLEAN",
        "default": 1
    },
    "condition_type": {
        "type": "VARCHAR(100)"
    },
    "item_no": {
        "type": "VARCHAR(100)"
    },
    "customer": {
        "type": "VARCHAR(100)"
    },
    "customer_grp": {
        "type": "INT"
    },
    "customer_hierarchy": {
        "type": "INT"
    },
    "distribution_channel_code": {
        "type": "INT"
    },
    "location_code": {
        "type": "INT"
    },
    "priority": {
        "type": "INT"
    },
    "currency": {
        "type": "VARCHAR(100)"
    },
    "sales_price": {
        "type": "FLOAT"
    },
    "unit_of_measure": {
        "type": "VARCHAR(100)"
    },
    "minimum_quantity": {
        "type": "INT"
    },
    "starting_date": {
        "type": "DATETIME"
    },
    "ending_date": {
        "type": "DATETIME"
    },
    "lower_limit": {
        "type": "FLOAT"
    },
    "upper_limit": {
        "type": "FLOAT"
    },
    "transportation_zone_code": {
        "type": "VARCHAR(100)"
    },
    "map": {
        "type": "VARCHAR(100)"
    },
    "change_type": {
        "type": "VARCHAR(100)"
    },
    "updated_from_sap": {
        "type": "BOOLEAN"
    },
    "sales_division_code": {
        "type": "INT"
    },
    "offer_article": {
        "type": "BOOLEAN"
    },
    "price_with_tax": {
        "type": "FLOAT"
    },
    "tax_percent": {
        "type": "FLOAT"
    },
    "created": {
        "type": "DATETIME",
        "default": "CURRENT_TIMESTAMP"
    },
    "updated": {
        "type": "DATETIME",
        "default": "CURRENT_TIMESTAMP",
        "on_update": "CURRENT_TIMESTAMP"
    },
    "indexes": {
        "idx_item_uom": {
            "type": "INDEX",
            "columns": [
                "item_no",
                "unit_of_measure"
            ]
        },
        "idx_dates": {
            "type": "INDEX",
            "columns": [
                "starting_date",
                "ending_date"
            ]
        }
    },
    "engine": "InnoDB",
    "charset": "utf8mb4"
}

Pricing_Location = {
    "id": {
        "type": "INT",
        "auto_increment": True,
        "primary_key": True
    },
    "location": {
        "type": "INT",
        "not_null": True
    },
    "is_active": {
        "type": "TINYINT(1)",
        "not_null": True,
        "default": 1
    },
    "created_at": {
        "type": "DATETIME",
        "not_null": True,
        "default": "CURRENT_TIMESTAMP"
    },
    "updated_at": {
        "type": "DATETIME",
        "not_null": True,
        "default": "CURRENT_TIMESTAMP",
        "on_update": "CURRENT_TIMESTAMP"
    },
    "indexes": {
        "uq_location": {
            "type": "UNIQUE",
            "columns": [
                "location"
            ]
        },
        "idx_location_active": {
            "type": "INDEX",
            "columns": [
                "location",
                "is_active"
            ]
        }
    },
    "engine": "InnoDB",
    "charset": "utf8mb4"
}

Pricing_Distribution_Channel = {
    "id": {
        "type": "INT",
        "auto_increment": True,
        "primary_key": True
    },
    "distribution_channel_code": {
        "type": "VARCHAR(20)",
        "not_null": True
    },
    "is_active": {
        "type": "TINYINT(1)",
        "not_null": True,
        "default": 1
    },
    "created_at": {
        "type": "DATETIME",
        "not_null": True,
        "default": "CURRENT_TIMESTAMP"
    },
    "updated_at": {
        "type": "DATETIME",
        "not_null": True,
        "default": "CURRENT_TIMESTAMP",
        "on_update": "CURRENT_TIMESTAMP"
    },
    "indexes": {
        "uq_distribution_channel": {
            "type": "UNIQUE",
            "columns": [
                "distribution_channel_code"
            ]
        },
        "idx_distribution_channel_active": {
            "type": "INDEX",
            "columns": [
                "distribution_channel_code",
                "is_active"
            ]
        }
    },
    "engine": "InnoDB",
    "charset": "utf8mb4"
}

Pricing_Priority = {
    "id": {
        "type": "INT",
        "auto_increment": True,
        "primary_key": True
    },
    "priority": {
        "type": "INT",
        "not_null": True
    },
    "is_active": {
        "type": "TINYINT(1)",
        "not_null": True,
        "default": 1
    },
    "created_at": {
        "type": "DATETIME",
        "not_null": True,
        "default": "CURRENT_TIMESTAMP"
    },
    "updated_at": {
        "type": "DATETIME",
        "not_null": True,
        "default": "CURRENT_TIMESTAMP",
        "on_update": "CURRENT_TIMESTAMP"
    },
    "indexes": {
        "uq_priority": {
            "type": "UNIQUE",
            "columns": [
                "priority"
            ]
        },
        "idx_priority_active": {
            "type": "INDEX",
            "columns": [
                "priority",
                "is_active"
            ]
        }
    },
    "engine": "InnoDB",
    "charset": "utf8mb4"
}

Pricing_Currency = {
    "id": {
        "type": "INT",
        "auto_increment": True,
        "primary_key": True
    },
    "currency": {
        "type": "VARCHAR(20)",
        "not_null": True
    },
    "is_active": {
        "type": "TINYINT(1)",
        "not_null": True,
        "default": 1
    },
    "created_at": {
        "type": "DATETIME",
        "not_null": True,
        "default": "CURRENT_TIMESTAMP"
    },
    "updated_at": {
        "type": "DATETIME",
        "not_null": True,
        "default": "CURRENT_TIMESTAMP",
        "on_update": "CURRENT_TIMESTAMP"
    },
    "indexes": {
        "uq_currency": {
            "type": "UNIQUE",
            "columns": [
                "currency"
            ]
        },
        "idx_currency_active": {
            "type": "INDEX",
            "columns": [
                "currency",
                "is_active"
            ]
        }
    },
    "engine": "InnoDB",
    "charset": "utf8mb4"
}

Pricing_Transportation_Zone = {
    "id": {
        "type": "INT",
        "auto_increment": True,
        "primary_key": True
    },
    "transportation_zone_code": {
        "type": "VARCHAR(20)",
        "not_null": True
    },
    "is_active": {
        "type": "TINYINT(1)",
        "not_null": True,
        "default": 1
    },
    "created_at": {
        "type": "DATETIME",
        "not_null": True,
        "default": "CURRENT_TIMESTAMP"
    },
    "updated_at": {
        "type": "DATETIME",
        "not_null": True,
        "default": "CURRENT_TIMESTAMP",
        "on_update": "CURRENT_TIMESTAMP"
    },
    "indexes": {
        "uq_transportation_zone": {
            "type": "UNIQUE",
            "columns": [
                "transportation_zone_code"
            ]
        },
        "idx_transportation_zone_active": {
            "type": "INDEX",
            "columns": [
                "transportation_zone_code",
                "is_active"
            ]
        }
    },
    "engine": "InnoDB",
    "charset": "utf8mb4"
}

Pricing_UOM = {
    "id": {
        "type": "INT",
        "auto_increment": True,
        "primary_key": True
    },
    "UOM": {
        "type": "VARCHAR(20)",
        "not_null": True
    },
    "is_active": {
        "type": "TINYINT(1)",
        "not_null": True,
        "default": 1
    },
    "created_at": {
        "type": "DATETIME",
        "not_null": True,
        "default": "CURRENT_TIMESTAMP"
    },
    "updated_at": {
        "type": "DATETIME",
        "not_null": True,
        "default": "CURRENT_TIMESTAMP",
        "on_update": "CURRENT_TIMESTAMP"
    },
    "indexes": {
        "uq_uom": {
            "type": "UNIQUE",
            "columns": [
                "UOM"
            ]
        },
        "idx_uom_active": {
            "type": "INDEX",
            "columns": [
                "UOM",
                "is_active"
            ]
        }
    },
    "engine": "InnoDB",
    "charset": "utf8mb4"
}

logger_table = {
    "id": {
        "type": "INT",
        "auto_increment": True,
        "primary_key": True
    },
    "ipaddress": {
        "type": "VARCHAR(50)",
        "not_null": True
    },
    "log_details": {
        "type" : "VARCHAR(100)",
        "not_null": True
    },
    "log_files": {
        "type" : "VARCHAR(300)",
        "not_null": True
    },
    "created_at": {
        "type": "DATETIME",
        "not_null": True,
        "default": "CURRENT_TIMESTAMP"
    },
}

#Discount Items Fields
Discount_Table = {
    "id": {
        "type": "INT",
        "auto_increment": True,
        "primary_key": True
    },
    "active": {
        "type": "BOOLEAN",
        "default": 1
    },
    "condition_type": {
        "type": "VARCHAR(100)"
    },
    "item_no": {
        "type": "VARCHAR(100)"
    },
    "customer": {
        "type": "VARCHAR(100)"
    },
    "customer_grp": {
        "type": "INT"
    },
    "customer_hierarchy": {
        "type": "INT"
    },
    "distribution_channel_code": {
        "type": "INT"
    },
    "location_code": {
        "type": "INT"
    },
    "priority": {
        "type": "INT"
    },
    "currency": {
        "type": "VARCHAR(100)"
    },
    "sales_price": {
        "type": "FLOAT"
    },
    "unit_of_measure": {
        "type": "VARCHAR(100)"
    },
    "minimum_quantity": {
        "type": "INT"
    },
    "starting_date": {
        "type": "DATE"
    },
    "ending_date": {
        "type": "DATE"
    },
    "lower_limit": {
        "type": "FLOAT"
    },
    "upper_limit": {
        "type": "FLOAT"
    },
    "transportation_zone_code": {
        "type": "VARCHAR(100)"
    },
    "map": {
        "type": "VARCHAR(100)"
    },
    "change_type": {
        "type": "VARCHAR(100)"
    },
    "updated_from_sap": {
        "type": "BOOLEAN"
    },
    "sales_division_code": {
        "type": "INT"
    },
    "offer_article": {
        "type": "BOOLEAN"
    },
    "price_with_tax": {
        "type": "FLOAT"
    },
    "tax_percent": {
        "type": "FLOAT"
    },
    "indexes": {
        "idx_item_uom": {
            "type": "INDEX",
            "columns": [
                "item_no",
                "unit_of_measure"
            ]
        },
        "idx_dates": {
            "type": "INDEX",
            "columns": [
                "starting_date",
                "ending_date"
            ]
        }
    },
    "engine": "InnoDB",
    "charset": "utf8mb4"
}

Discount_Location = {
    "id": {
        "type": "INT",
        "auto_increment": True,
        "primary_key": True
    },
    "location": {
        "type": "INT",
        "not_null": True
    },
    "is_active": {
        "type": "TINYINT(1)",
        "not_null": True,
        "default": 1
    },
    "created_at": {
        "type": "DATETIME",
        "not_null": True,
        "default": "CURRENT_TIMESTAMP"
    },
    "updated_at": {
        "type": "DATETIME",
        "not_null": True,
        "default": "CURRENT_TIMESTAMP",
        "on_update": "CURRENT_TIMESTAMP"
    },
    "indexes": {
        "uq_location": {
            "type": "UNIQUE",
            "columns": [
                "location"
            ]
        },
        "idx_location_active": {
            "type": "INDEX",
            "columns": [
                "location",
                "is_active"
            ]
        }
    },
    "engine": "InnoDB",
    "charset": "utf8mb4"
}

Discount_Distribution_Channel = {
    "id": {
        "type": "INT",
        "auto_increment": True,
        "primary_key": True
    },
    "distribution_channel_code": {
        "type": "VARCHAR(20)",
        "not_null": True
    },
    "is_active": {
        "type": "TINYINT(1)",
        "not_null": True,
        "default": 1
    },
    "created_at": {
        "type": "DATETIME",
        "not_null": True,
        "default": "CURRENT_TIMESTAMP"
    },
    "updated_at": {
        "type": "DATETIME",
        "not_null": True,
        "default": "CURRENT_TIMESTAMP",
        "on_update": "CURRENT_TIMESTAMP"
    },
    "indexes": {
        "uq_distribution_channel": {
            "type": "UNIQUE",
            "columns": [
                "distribution_channel_code"
            ]
        },
        "idx_distribution_channel_active": {
            "type": "INDEX",
            "columns": [
                "distribution_channel_code",
                "is_active"
            ]
        }
    },
    "engine": "InnoDB",
    "charset": "utf8mb4"
}

Discount_Priority = {
    "id": {
        "type": "INT",
        "auto_increment": True,
        "primary_key": True
    },
    "priority": {
        "type": "INT",
        "not_null": True
    },
    "is_active": {
        "type": "TINYINT(1)",
        "not_null": True,
        "default": 1
    },
    "created_at": {
        "type": "DATETIME",
        "not_null": True,
        "default": "CURRENT_TIMESTAMP"
    },
    "updated_at": {
        "type": "DATETIME",
        "not_null": True,
        "default": "CURRENT_TIMESTAMP",
        "on_update": "CURRENT_TIMESTAMP"
    },
    "indexes": {
        "uq_priority": {
            "type": "UNIQUE",
            "columns": [
                "priority"
            ]
        },
        "idx_priority_active": {
            "type": "INDEX",
            "columns": [
                "priority",
                "is_active"
            ]
        }
    },
    "engine": "InnoDB",
    "charset": "utf8mb4"
}

Discount_Currency = {
    "id": {
        "type": "INT",
        "auto_increment": True,
        "primary_key": True
    },
    "currency": {
        "type": "VARCHAR(20)",
        "not_null": True
    },
    "is_active": {
        "type": "TINYINT(1)",
        "not_null": True,
        "default": 1
    },
    "created_at": {
        "type": "DATETIME",
        "not_null": True,
        "default": "CURRENT_TIMESTAMP"
    },
    "updated_at": {
        "type": "DATETIME",
        "not_null": True,
        "default": "CURRENT_TIMESTAMP",
        "on_update": "CURRENT_TIMESTAMP"
    },
    "indexes": {
        "uq_currency": {
            "type": "UNIQUE",
            "columns": [
                "currency"
            ]
        },
        "idx_currency_active": {
            "type": "INDEX",
            "columns": [
                "currency",
                "is_active"
            ]
        }
    },
    "engine": "InnoDB",
    "charset": "utf8mb4"
}

Discount_Transportation_Zone = {
    "id": {
        "type": "INT",
        "auto_increment": True,
        "primary_key": True
    },
    "transportation_zone_code": {
        "type": "VARCHAR(20)",
        "not_null": True
    },
    "is_active": {
        "type": "TINYINT(1)",
        "not_null": True,
        "default": 1
    },
    "created_at": {
        "type": "DATETIME",
        "not_null": True,
        "default": "CURRENT_TIMESTAMP"
    },
    "updated_at": {
        "type": "DATETIME",
        "not_null": True,
        "default": "CURRENT_TIMESTAMP",
        "on_update": "CURRENT_TIMESTAMP"
    },
    "indexes": {
        "uq_transportation_zone": {
            "type": "UNIQUE",
            "columns": [
                "transportation_zone_code"
            ]
        },
        "idx_transportation_zone_active": {
            "type": "INDEX",
            "columns": [
                "transportation_zone_code",
                "is_active"
            ]
        }
    },
    "engine": "InnoDB",
    "charset": "utf8mb4"
}

Discount_UOM = {
    "id": {
        "type": "INT",
        "auto_increment": True,
        "primary_key": True
    },
    "UOM": {
        "type": "VARCHAR(20)",
        "not_null": True
    },
    "is_active": {
        "type": "TINYINT(1)",
        "not_null": True,
        "default": 1
    },
    "created_at": {
        "type": "DATETIME",
        "not_null": True,
        "default": "CURRENT_TIMESTAMP"
    },
    "updated_at": {
        "type": "DATETIME",
        "not_null": True,
        "default": "CURRENT_TIMESTAMP",
        "on_update": "CURRENT_TIMESTAMP"
    },
    "indexes": {
        "uq_uom": {
            "type": "UNIQUE",
            "columns": [
                "UOM"
            ]
        },
        "idx_uom_active": {
            "type": "INDEX",
            "columns": [
                "UOM",
                "is_active"
            ]
        }
    },
    "engine": "InnoDB",
    "charset": "utf8mb4"
}
