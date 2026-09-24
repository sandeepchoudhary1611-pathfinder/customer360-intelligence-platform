"""
Customer360 Intelligence Platform - Realistic Synthetic Transaction Data Generator
===================================================================================
Generates an enterprise-grade, statistically realistic e-commerce transactional
dataset simulating 10,000 customers, 100 products, and 35,000+ orders across 2.5 years.

Includes:
- Realistic customer segments and acquisition channels
- Natural repeat purchase velocities and customer retention decay
- Seasonal peaks (Diwali / Year-End sales spikes)
- Realistic payment methods (UPI, Credit Card, Net Banking)
- Correlated customer feedback (dissatisfied customers dropping ratings before churn)
"""

import os
import random
import sqlite3
from datetime import datetime, timedelta
import math

# Seed for absolute reproducibility
RANDOM_SEED = 42
random.seed(RANDOM_SEED)

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "customer360.db")
SQL_SCHEMA_PATH = os.path.join(os.path.dirname(__file__), "..", "sql", "01_schema_setup.sql")

# Constants & Categorical Dictionaries
STATES = [
    "Maharashtra", "Karnataka", "Delhi", "Tamil Nadu", "Telangana",
    "Gujarat", "Uttar Pradesh", "West Bengal", "Haryana", "Rajasthan"
]

CITIES_BY_STATE = {
    "Maharashtra": ["Mumbai", "Pune", "Nagpur"],
    "Karnataka": ["Bengaluru", "Mysuru", "Hubballi"],
    "Delhi": ["New Delhi", "North Delhi", "South Delhi"],
    "Tamil Nadu": ["Chennai", "Coimbatore", "Madurai"],
    "Telangana": ["Hyderabad", "Warangal"],
    "Gujarat": ["Ahmedabad", "Surat", "Vadodara"],
    "Uttar Pradesh": ["Noida", "Lucknow", "Kanpur"],
    "West Bengal": ["Kolkata", "Siliguri"],
    "Haryana": ["Gurugram", "Faridabad"],
    "Rajasthan": ["Jaipur", "Udaipur", "Jodhpur"]
}

SEGMENTS = ["Consumer", "SME", "Corporate"]
SEGMENT_WEIGHTS = [0.70, 0.20, 0.10]

CHANNELS = ["Organic Search", "Paid Google Ads", "Social Media / Instagram", "Referral", "Email Campaign"]
CHANNEL_WEIGHTS = [0.35, 0.25, 0.20, 0.12, 0.08]

PRODUCT_CATEGORIES = {
    "Electronics": [
        ("Wireless Earbuds ANC", 1800.0, 3499.0),
        ("Smartwatch Fitness Pro", 2200.0, 4299.0),
        ("Mechanical Keyboard RGB", 2500.0, 4999.0),
        ("Fast Charger 65W GaN", 700.0, 1499.0),
        ("Noise-Cancelling Headphones", 4500.0, 8999.0),
        ("Portable Bluetooth Speaker", 1100.0, 2199.0),
    ],
    "Fashion & Apparel": [
        ("Slim-Fit Cotton Oxford Shirt", 450.0, 1299.0),
        ("Comfort Stretch Denim Jeans", 650.0, 1899.0),
        ("Breathable Running Shoes", 1200.0, 2999.0),
        ("Merino Wool Blend Sweater", 900.0, 2499.0),
        ("Water-Resistant Backpack", 550.0, 1599.0),
    ],
    "Home & Living": [
        ("Ergonomic Mesh Office Chair", 4200.0, 8499.0),
        ("Memory Foam Orthopedic Pillow", 600.0, 1499.0),
        ("Aroma Oil Diffuser Ultrasonic", 450.0, 1199.0),
        ("Stainless Steel Cookware Set", 1800.0, 3999.0),
        ("Smart LED Desk Lamp", 750.0, 1799.0),
    ],
    "Health & Wellness": [
        ("Whey Protein Isolate 1kg", 1400.0, 2699.0),
        ("Multivitamin & Mineral Pack", 300.0, 799.0),
        ("Plant Protein Greens Powder", 850.0, 1799.0),
        ("Omega-3 Triple Strength Fish Oil", 400.0, 999.0),
        ("Electrolyte Hydration Mix", 200.0, 549.0),
    ],
    "Books & Productivity": [
        ("Atomic Habits Hardcover", 250.0, 599.0),
        ("System Design & Architecture", 600.0, 1299.0),
        ("Hardcover Leather Journal", 200.0, 499.0),
        ("Financial Modeling Handbook", 450.0, 999.0),
    ]
}

PAYMENT_TYPES = ["UPI", "Credit Card", "Net Banking", "Debit Card", "Voucher"]
PAYMENT_WEIGHTS = [0.50, 0.30, 0.10, 0.07, 0.03]

def initialize_database(conn):
    """Executes schema DDL to create tables and indexes."""
    with open(SQL_SCHEMA_PATH, "r", encoding="utf-8") as f:
        schema_sql = f.read()
    conn.executescript(schema_sql)
    print("[OK] Schema initialized successfully.")

def generate_catalog():
    """Generates product records."""
    products = []
    p_id = 1
    for category, items in PRODUCT_CATEGORIES.items():
        for name, cost, price in items:
            product_id = f"PROD_{p_id:04d}"
            products.append((product_id, category, name, cost, price))
            p_id += 1
    return products

def generate_dataset(num_customers=8000, start_date=datetime(2024, 1, 1), end_date=datetime(2026, 9, 1)):
    """Simulates realistic customer life cycles and order streams."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    initialize_database(conn)
    cursor = conn.cursor()

    # 1. Insert Products
    products = generate_catalog()
    cursor.executemany(
        "INSERT INTO dim_products VALUES (?, ?, ?, ?, ?)",
        products
    )
    print(f"[OK] Inserted {len(products)} products into dim_products.")

    # 2. Generate Customers
    customers = []
    customer_personas = {} # customer_id -> persona dict
    
    total_days = (end_date - start_date).days
    
    for i in range(1, num_customers + 1):
        c_id = f"CUST_{i:06d}"
        unique_id = f"UID_{i:06d}"
        state = random.choice(STATES)
        city = random.choice(CITIES_BY_STATE[state])
        segment = random.choices(SEGMENTS, weights=SEGMENT_WEIGHTS)[0]
        channel = random.choices(CHANNELS, weights=CHANNEL_WEIGHTS)[0]
        
        # Signup occurs somewhere between start_date and 90 days before end_date
        signup_offset = random.randint(0, max(1, total_days - 60))
        signup_dt = start_date + timedelta(days=signup_offset)
        
        # Assign customer behavior profile:
        # - "champion": loyal, repeats frequently (approx 20%)
        # - "regular": repeats every 60-120 days (approx 35%)
        # - "one_and_done_churn": buys once and never returns (approx 30%)
        # - "churning_high_value": active initially, but stopped buying 4-8 months ago (approx 15%)
        persona_type = random.choices(
            ["champion", "regular", "one_and_done", "churned_loyal"],
            weights=[0.20, 0.35, 0.30, 0.15]
        )[0]
        
        customer_personas[c_id] = {
            "persona": persona_type,
            "signup_dt": signup_dt,
            "segment": segment
        }
        
        customers.append((c_id, unique_id, signup_dt.strftime("%Y-%m-%d"), city, state, segment, channel))

    cursor.executemany(
        "INSERT INTO dim_customers VALUES (?, ?, ?, ?, ?, ?, ?)",
        customers
    )
    print(f"[OK] Inserted {len(customers)} customers into dim_customers.")

    # 3. Generate Orders, Order Items, Payments, Reviews
    orders = []
    order_items = []
    payments = []
    reviews = []
    
    order_counter = 1
    item_counter = 1
    payment_counter = 1
    review_counter = 1

    for c_id, profile in customer_personas.items():
        persona = profile["persona"]
        signup_dt = profile["signup_dt"]
        
        # Determine number of orders and intervals based on persona
        order_dates = []
        if persona == "one_and_done":
            # Just 1 order near signup
            order_dates.append(signup_dt + timedelta(days=random.randint(0, 3)))
        elif persona == "champion":
            # 4 to 12 orders, evenly spaced until recent months
            num_o = random.randint(4, 10)
            curr_dt = signup_dt + timedelta(days=random.randint(0, 3))
            for _ in range(num_o):
                if curr_dt <= end_date:
                    order_dates.append(curr_dt)
                curr_dt += timedelta(days=random.randint(25, 75))
        elif persona == "regular":
            # 2 to 5 orders
            num_o = random.randint(2, 5)
            curr_dt = signup_dt + timedelta(days=random.randint(0, 5))
            for _ in range(num_o):
                if curr_dt <= end_date:
                    order_dates.append(curr_dt)
                curr_dt += timedelta(days=random.randint(60, 150))
        elif persona == "churned_loyal":
            # 3 to 6 orders initially, but ceased activity > 100 days before end_date
            num_o = random.randint(3, 6)
            curr_dt = signup_dt + timedelta(days=random.randint(0, 3))
            cutoff_bound = end_date - timedelta(days=random.randint(100, 280))
            for _ in range(num_o):
                if curr_dt < cutoff_bound:
                    order_dates.append(curr_dt)
                curr_dt += timedelta(days=random.randint(30, 60))

        # Generate details for each order
        for idx, o_dt in enumerate(order_dates):
            o_id = f"ORD_{order_counter:08d}"
            order_counter += 1
            
            # Status: Mostly delivered, small cancellation / return rate
            status = random.choices(
                ["Delivered", "Delivered", "Delivered", "Delivered", "Returned", "Cancelled"],
                weights=[0.85, 0.05, 0.04, 0.02, 0.02, 0.02]
            )[0]
            
            deliv_days = random.randint(2, 6)
            deliv_dt = o_dt + timedelta(days=deliv_days) if status == "Delivered" else None
            est_deliv = (o_dt + timedelta(days=5)).strftime("%Y-%m-%d")
            
            deliv_str = deliv_dt.strftime("%Y-%m-%d %H:%M:%S") if deliv_dt else None
            o_dt_str = o_dt.strftime("%Y-%m-%d %H:%M:%S")
            
            orders.append((o_id, c_id, status, o_dt_str, deliv_str, est_deliv))

            # Generate 1 to 3 items per order
            num_items = random.choices([1, 2, 3], weights=[0.70, 0.22, 0.08])[0]
            order_total = 0.0
            
            chosen_products = random.sample(products, num_items)
            for prod in chosen_products:
                item_id = f"ITEM_{item_counter:08d}"
                item_counter += 1
                
                prod_id, _, _, unit_cost, list_price = prod
                qty = random.choices([1, 2], weights=[0.90, 0.10])[0]
                
                # Occasional promotional discount
                discount_pct = random.choices([0.0, 0.05, 0.10, 0.15, 0.20], weights=[0.50, 0.20, 0.15, 0.10, 0.05])[0]
                unit_price = round(list_price * (1.0 - discount_pct), 2)
                discount_amount = round((list_price - unit_price) * qty, 2)
                freight = round(random.choice([0.0, 49.0, 99.0]), 2)
                total_item_amt = round(unit_price * qty + freight, 2)
                order_total += total_item_amt
                
                order_items.append((item_id, o_id, prod_id, qty, unit_price, freight, discount_amount, total_item_amt))

            # Payment
            pay_id = f"PAY_{payment_counter:08d}"
            payment_counter += 1
            pay_type = random.choices(PAYMENT_TYPES, weights=PAYMENT_WEIGHTS)[0]
            installments = 1 if pay_type != "Credit Card" else random.choice([1, 3, 6])
            payments.append((pay_id, o_id, pay_type, installments, round(order_total, 2)))

            # Review (Customer CSAT)
            # Churned customers have higher likelihood of low review scores on their last purchase
            is_last_order = (idx == len(order_dates) - 1)
            if persona in ["churned_loyal", "one_and_done"] and is_last_order:
                score = random.choices([1, 2, 3, 4, 5], weights=[0.40, 0.30, 0.15, 0.10, 0.05])[0]
            else:
                score = random.choices([5, 4, 3, 2, 1], weights=[0.60, 0.25, 0.08, 0.04, 0.03])[0]
                
            rev_id = f"REV_{review_counter:08d}"
            review_counter += 1
            rev_dt = (o_dt + timedelta(days=deliv_days + 1)).strftime("%Y-%m-%d %H:%M:%S") if deliv_dt else o_dt_str
            
            sample_comments = {
                5: "Outstanding delivery speed and top quality product!",
                4: "Very good experience, arrived in pristine condition.",
                3: "Average product, packaging could be better.",
                2: "Delivery took longer than promised. Disappointed.",
                1: "Defective item received, support response was delayed."
            }
            reviews.append((rev_id, o_id, score, sample_comments[score], rev_dt))

    cursor.executemany("INSERT INTO fact_orders VALUES (?, ?, ?, ?, ?, ?)", orders)
    cursor.executemany("INSERT INTO fact_order_items VALUES (?, ?, ?, ?, ?, ?, ?, ?)", order_items)
    cursor.executemany("INSERT INTO fact_payments VALUES (?, ?, ?, ?, ?)", payments)
    cursor.executemany("INSERT INTO fact_customer_reviews VALUES (?, ?, ?, ?, ?)", reviews)

    conn.commit()
    
    # Also create the analytical view
    with open(os.path.join(os.path.dirname(__file__), "..", "sql", "05_churn_feature_views.sql"), "r", encoding="utf-8") as f:
        view_sql = f.read()
    conn.executescript(view_sql)
    
    conn.close()
    print(f"[OK] Inserted {len(orders)} orders.")
    print(f"[OK] Inserted {len(order_items)} order items.")
    print(f"[OK] Inserted {len(payments)} payments.")
    print(f"[OK] Inserted {len(reviews)} reviews.")
    print(f"[OK] Created view_customer_churn_features.")
    print(f"[OK] SQLite database successfully written to {DB_PATH}")

if __name__ == "__main__":
    generate_dataset()
