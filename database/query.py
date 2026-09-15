# Database Creation query for Pricing and Discount
def create_pricing_database_query(db_name):
    return f"CREATE DATABASE IF NOT EXISTS {db_name}"

#
def create_pricing_table_query(table_name):
    return f"""
        CREATE TABLE IF NOT EXISTS {table_name} (
            id INT AUTO_INCREMENT PRIMARY KEY,
            active BOOLEAN DEFAULT 1,
            condition_type VARCHAR(100),
            item_no VARCHAR(100),
            customer VARCHAR(100),
            customer_grp INT,
            customer_hierarchy INT,
            distribution_channel_code INT,
            location_code INT,
            priority INT,
            currency VARCHAR(100),
            sales_price FLOAT,
            unit_of_measure VARCHAR(100),
            minimum_quantity INT,
            starting_date DATETIME,
            ending_date DATETIME,
            lower_limit FLOAT,
            upper_limit FLOAT,
            transportation_zone_code VARCHAR(100),
            map VARCHAR(100),
            change_type VARCHAR(100),
            updated_from_sap BOOLEAN,
            sales_division_code INT,
            offer_article BOOLEAN,
            price_with_tax FLOAT,
            tax_percent FLOAT,
            KEY idx_item_uom (item_no, unit_of_measure),
            KEY idx_dates (starting_date, ending_date)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """

def select_all_prices(page, limit):
    offset = (page - 1) * limit
    sql_query = """
        SELECT *
        FROM PRICING_TABLE
        ORDER BY item_no
        LIMIT %s OFFSET %s
    """
    return sql_query, (limit, offset)
 
def insert_price_query(data):
    sql_query = """
        INSERT INTO PRICING_TABLE (
            active,
            condition_type,
            item_no,
            customer,
            customer_grp,
            customer_hierarchy,
            distribution_channel_code,
            location_code,
            priority,
            currency,
            sales_price,
            unit_of_measure,
            minimum_quantity,
            starting_date,
            ending_date,
            lower_limit,
            upper_limit,
            transportation_zone_code,
            map,
            change_type,
            updated_from_sap,
            sales_division_code,
            offer_article,
            price_with_tax,
            tax_percent
        )
        VALUES (
            %s, %s, %s, %s, %s,
            %s, %s, %s, %s, %s,
            %s, %s, %s, %s, %s,
            %s, %s, %s, %s, %s,
            %s, %s, %s, %s, %s
        )
    """
    params = (
        data.get("active"),
        data.get("condition_type"),
        data.get("item_no"),
        data.get("customer"),
        data.get("customer_grp"),
        data.get("customer_hierarchy"),
        data.get("distribution_channel_code"),
        data.get("location_code"),
        data.get("priority"),
        data.get("currency"),
        data.get("sales_price"),
        data.get("unit_of_measure"),
        data.get("minimum_quantity"),
        data.get("starting_date"),
        data.get("ending_date"),
        data.get("lower_limit"),
        data.get("upper_limit"),
        data.get("transportation_zone_code"),
        data.get("map"),
        data.get("change_type"),
        data.get("updated_from_sap"),
        data.get("sales_division_code"),
        data.get("offer_article"),
        data.get("price_with_tax"),
        data.get("tax_percent"),
    )
    return sql_query, params
 
def update_price(price_id, data):
    sql_query = """
        UPDATE PRICING_TABLE
        SET
            active = %s,
            condition_type = %s,
            item_no = %s,
            customer = %s,
            customer_grp = %s,
            customer_hierarchy = %s,
            distribution_channel_code = %s,
            location_code = %s,
            priority = %s,
            currency = %s,
            sales_price = %s,
            unit_of_measure = %s,
            minimum_quantity = %s,
            starting_date = %s,
            ending_date = %s,
            lower_limit = %s,
            upper_limit = %s,
            transportation_zone_code = %s,
            map = %s,
            change_type = %s,
            updated_from_sap = %s,
            sales_division_code = %s,
            offer_article = %s,
            price_with_tax = %s,
            tax_percent = %s
        WHERE id = %s
    """
    params = (
        data.get("active"),
        data.get("condition_type"),
        data.get("item_no"),
        data.get("customer"),
        data.get("customer_grp"),
        data.get("customer_hierarchy"),
        data.get("distribution_channel_code"),
        data.get("location_code"),
        data.get("priority"),
        data.get("currency"),
        data.get("sales_price"),
        data.get("unit_of_measure"),
        data.get("minimum_quantity"),
        data.get("starting_date"),
        data.get("ending_date"),
        data.get("lower_limit"),
        data.get("upper_limit"),
        data.get("transportation_zone_code"),
        data.get("map"),
        data.get("change_type"),
        data.get("updated_from_sap"),
        data.get("sales_division_code"),
        data.get("offer_article"),
        data.get("price_with_tax"),
        data.get("tax_percent"),
        price_id
    )
    return sql_query, params
 
def check_price_exists(price_id):
    sql_query = """
        SELECT id
        FROM PRICING_TABLE
        WHERE id = %s
    """
    params = (price_id,)
    return sql_query, params
 
def filter_prices(data):
    sql_query = """
        SELECT *
        FROM PRICING_TABLE
        WHERE TRUE
    """
    params = []
    if data.get("active") is not None:
        sql_query += " AND active = %s"
        params.append(data.get("active"))
    if data.get("condition_type"):
        sql_query += " AND condition_type = %s"
        params.append(data.get("condition_type"))
    if data.get("item_no"):
        sql_query += " AND item_no = %s"
        params.append(data.get("item_no"))
    if data.get("customer"):
        sql_query += " AND customer = %s"
        params.append(data.get("customer"))
    if data.get("customer_grp") is not None:
        sql_query += " AND customer_grp = %s"
        params.append(data.get("customer_grp"))
    if data.get("customer_hierarchy") is not None:
        sql_query += " AND customer_hierarchy = %s"
        params.append(data.get("customer_hierarchy"))
    if data.get("distribution_channel_code") is not None:
        sql_query += " AND distribution_channel_code = %s"
        params.append(data.get("distribution_channel_code"))
    if data.get("location_code") is not None:
        sql_query += " AND location_code = %s"
        params.append(data.get("location_code"))
    if data.get("priority") is not None:
        sql_query += " AND priority = %s"
        params.append(data.get("priority"))
    if data.get("currency"):
        sql_query += " AND currency = %s"
        params.append(data.get("currency"))
    if data.get("sales_price") is not None:
        sql_query += " AND sales_price = %s"
        params.append(data.get("sales_price"))
    if data.get("unit_of_measure"):
        sql_query += " AND unit_of_measure = %s"
        params.append(data.get("unit_of_measure"))
    if data.get("minimum_quantity") is not None:
        sql_query += " AND minimum_quantity = %s"
        params.append(data.get("minimum_quantity"))
    if data.get("starting_date"):
        sql_query += " AND starting_date = %s"
        params.append(data.get("starting_date"))
    if data.get("ending_date"):
        sql_query += " AND ending_date = %s"
        params.append(data.get("ending_date"))
    if data.get("lower_limit") is not None:
        sql_query += " AND lower_limit = %s"
        params.append(data.get("lower_limit"))
    if data.get("upper_limit") is not None:
        sql_query += " AND upper_limit = %s"
        params.append(data.get("upper_limit"))
    if data.get("transportation_zone_code"):
        sql_query += " AND transportation_zone_code = %s"
        params.append(data.get("transportation_zone_code"))
    if data.get("map"):
        sql_query += " AND map = %s"
        params.append(data.get("map"))
    if data.get("change_type"):
        sql_query += " AND change_type = %s"
        params.append(data.get("change_type"))
    if data.get("updated_from_sap") is not None:
        sql_query += " AND updated_from_sap = %s"
        params.append(data.get("updated_from_sap"))
    if data.get("sales_division_code") is not None:
        sql_query += " AND sales_division_code = %s"
        params.append(data.get("sales_division_code"))
    if data.get("offer_article") is not None:
        sql_query += " AND offer_article = %s"
        params.append(data.get("offer_article"))
    if data.get("price_with_tax") is not None:
        sql_query += " AND price_with_tax = %s"
        params.append(data.get("price_with_tax"))
    if data.get("tax_percent") is not None:
        sql_query += " AND tax_percent = %s"
        params.append(data.get("tax_percent"))
    sql_query += " ORDER BY item_no"
    return sql_query, tuple(params)

def deactive_exp_items():
    sql_query = """
        update PRICING_TABLE set active = true where id=63
    """
    return sql_query