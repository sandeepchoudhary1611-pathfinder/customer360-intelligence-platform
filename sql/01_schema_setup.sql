-- ============================================================================
-- Customer360 Intelligence Platform - Database Schema (Star Schema)
-- Dialect: ANSI SQL / Compatible with SQLite, PostgreSQL, DuckDB
-- ============================================================================

-- Drop tables if already existing (for clean rebuilding)
DROP TABLE IF EXISTS fact_customer_reviews;
DROP TABLE IF EXISTS fact_payments;
DROP TABLE IF EXISTS fact_order_items;
DROP TABLE IF EXISTS fact_orders;
DROP TABLE IF EXISTS dim_products;
DROP TABLE IF EXISTS dim_customers;

-- ----------------------------------------------------------------------------
-- 1. Dimension: Customers
-- ----------------------------------------------------------------------------
CREATE TABLE dim_customers (
    customer_id VARCHAR(50) PRIMARY KEY,
    customer_unique_id VARCHAR(50) NOT NULL,
    signup_date DATE NOT NULL,
    customer_city VARCHAR(100),
    customer_state VARCHAR(50),
    customer_segment VARCHAR(50) DEFAULT 'Consumer', -- Consumer, Corporate, SME
    acquisition_channel VARCHAR(50) DEFAULT 'Organic' -- Organic, Paid Search, Social, Referral, Email
);

-- ----------------------------------------------------------------------------
-- 2. Dimension: Products
-- ----------------------------------------------------------------------------
CREATE TABLE dim_products (
    product_id VARCHAR(50) PRIMARY KEY,
    product_category VARCHAR(100) NOT NULL,
    product_subcategory VARCHAR(100),
    unit_cost DECIMAL(10, 2) NOT NULL,
    list_price DECIMAL(10, 2) NOT NULL
);

-- ----------------------------------------------------------------------------
-- 3. Fact: Orders
-- ----------------------------------------------------------------------------
CREATE TABLE fact_orders (
    order_id VARCHAR(50) PRIMARY KEY,
    customer_id VARCHAR(50) NOT NULL,
    order_status VARCHAR(30) NOT NULL, -- Delivered, Shipped, Cancelled, Returned
    order_purchase_timestamp TIMESTAMP NOT NULL,
    order_delivered_timestamp TIMESTAMP,
    order_estimated_delivery_date DATE,
    FOREIGN KEY (customer_id) REFERENCES dim_customers (customer_id)
);

-- ----------------------------------------------------------------------------
-- 4. Fact: Order Items (Line-level sales)
-- ----------------------------------------------------------------------------
CREATE TABLE fact_order_items (
    order_item_id VARCHAR(50) PRIMARY KEY,
    order_id VARCHAR(50) NOT NULL,
    product_id VARCHAR(50) NOT NULL,
    quantity INT NOT NULL DEFAULT 1,
    unit_price DECIMAL(10, 2) NOT NULL,
    freight_value DECIMAL(10, 2) DEFAULT 0.00,
    discount_amount DECIMAL(10, 2) DEFAULT 0.00,
    total_amount DECIMAL(10, 2) NOT NULL,
    FOREIGN KEY (order_id) REFERENCES fact_orders (order_id),
    FOREIGN KEY (product_id) REFERENCES dim_products (product_id)
);

-- ----------------------------------------------------------------------------
-- 5. Fact: Payments
-- ----------------------------------------------------------------------------
CREATE TABLE fact_payments (
    payment_id VARCHAR(50) PRIMARY KEY,
    order_id VARCHAR(50) NOT NULL,
    payment_type VARCHAR(50) NOT NULL, -- Credit Card, UPI, Net Banking, Voucher
    payment_installments INT DEFAULT 1,
    payment_value DECIMAL(10, 2) NOT NULL,
    FOREIGN KEY (order_id) REFERENCES fact_orders (order_id)
);

-- ----------------------------------------------------------------------------
-- 6. Fact: Customer Reviews / CSAT
-- ----------------------------------------------------------------------------
CREATE TABLE fact_customer_reviews (
    review_id VARCHAR(50) PRIMARY KEY,
    order_id VARCHAR(50) NOT NULL,
    review_score INT NOT NULL, -- 1 to 5
    review_comment_message TEXT,
    review_creation_date TIMESTAMP NOT NULL,
    FOREIGN KEY (order_id) REFERENCES fact_orders (order_id)
);

-- ----------------------------------------------------------------------------
-- Performance Indexes for Analytical Queries
-- ----------------------------------------------------------------------------
CREATE INDEX idx_orders_customer ON fact_orders(customer_id);
CREATE INDEX idx_orders_timestamp ON fact_orders(order_purchase_timestamp);
CREATE INDEX idx_order_items_order ON fact_order_items(order_id);
CREATE INDEX idx_order_items_product ON fact_order_items(product_id);
CREATE INDEX idx_payments_order ON fact_payments(order_id);
CREATE INDEX idx_reviews_order ON fact_customer_reviews(order_id);
