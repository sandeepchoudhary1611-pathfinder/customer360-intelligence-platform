-- ============================================================================
-- Customer360: Machine Learning Feature View for Customer Churn Modeling
-- Dialect: ANSI SQL / Compatible with SQLite, PostgreSQL, DuckDB
-- ============================================================================
-- Business Objective:
-- Build an enterprise-grade analytical feature view that transforms normalized
-- transactional data into flat, feature-rich customer observation records for
-- supervised machine learning (predicting 90-day churn).
-- ============================================================================

DROP VIEW IF EXISTS view_customer_churn_features;

CREATE VIEW view_customer_churn_features AS
WITH observation_snapshot AS (
    -- Reference timestamp for calculating recency and churn cutoff
    SELECT 
        MAX(order_purchase_timestamp) AS max_timestamp,
        DATE(MAX(order_purchase_timestamp), '-90 days') AS churn_cutoff_date
    FROM fact_orders
    WHERE order_status = 'Delivered'
),

customer_base_metrics AS (
    SELECT 
        c.customer_id,
        c.customer_segment,
        c.acquisition_channel,
        c.customer_state,
        c.signup_date,
        -- Total lifetime orders
        COUNT(DISTINCT o.order_id) AS total_orders_placed,
        -- Delivered orders count
        COUNT(DISTINCT CASE WHEN o.order_status = 'Delivered' THEN o.order_id END) AS completed_orders,
        -- Cancelled or returned orders count
        COUNT(DISTINCT CASE WHEN o.order_status IN ('Cancelled', 'Returned') THEN o.order_id END) AS failed_orders,
        -- First and last order dates
        MIN(o.order_purchase_timestamp) AS first_order_date,
        MAX(o.order_purchase_timestamp) AS last_order_date
    FROM dim_customers c
    LEFT JOIN fact_orders o ON c.customer_id = o.customer_id
    GROUP BY c.customer_id, c.customer_segment, c.acquisition_channel, c.customer_state, c.signup_date
),

customer_financial_metrics AS (
    SELECT 
        o.customer_id,
        SUM(oi.total_amount) AS total_spend,
        AVG(oi.total_amount) AS avg_item_price,
        SUM(oi.quantity) AS total_units_purchased,
        SUM(oi.discount_amount) AS total_discount_received,
        AVG(oi.discount_amount / NULLIF(oi.total_amount + oi.discount_amount, 0)) AS avg_discount_pct,
        COUNT(DISTINCT p.product_category) AS unique_categories_bought
    FROM fact_orders o
    INNER JOIN fact_order_items oi ON o.order_id = oi.order_id
    INNER JOIN dim_products p ON oi.product_id = p.product_id
    WHERE o.order_status = 'Delivered'
    GROUP BY o.customer_id
),

customer_payment_metrics AS (
    SELECT 
        o.customer_id,
        AVG(fp.payment_installments) AS avg_payment_installments,
        MAX(CASE WHEN fp.payment_type = 'Credit Card' THEN 1 ELSE 0 END) AS uses_credit_card,
        MAX(CASE WHEN fp.payment_type = 'UPI' THEN 1 ELSE 0 END) AS uses_upi
    FROM fact_orders o
    INNER JOIN fact_payments fp ON o.order_id = fp.order_id
    GROUP BY o.customer_id
),

customer_review_metrics AS (
    SELECT 
        o.customer_id,
        ROUND(AVG(r.review_score), 2) AS avg_csat_score,
        COUNT(CASE WHEN r.review_score <= 2 THEN 1 END) AS low_rating_count
    FROM fact_orders o
    INNER JOIN fact_customer_reviews r ON o.order_id = r.order_id
    GROUP BY o.customer_id
)

SELECT 
    b.customer_id,
    b.customer_segment,
    b.acquisition_channel,
    b.customer_state,
    
    -- Engagement Features
    b.total_orders_placed,
    b.completed_orders,
    b.failed_orders,
    CAST(JULIANDAY(s.max_timestamp) - JULIANDAY(b.last_order_date) AS INT) AS recency_days,
    CAST(JULIANDAY(b.last_order_date) - JULIANDAY(b.first_order_date) AS INT) AS customer_tenure_days,
    
    -- Monetary & Basket Features
    COALESCE(f.total_spend, 0.0) AS total_lifetime_spend,
    COALESCE(ROUND(f.total_spend / NULLIF(b.completed_orders, 0), 2), 0.0) AS average_order_value,
    COALESCE(f.total_units_purchased, 0) AS total_units_purchased,
    COALESCE(ROUND(f.avg_discount_pct * 100, 2), 0.0) AS discount_sensitivity_pct,
    COALESCE(f.unique_categories_bought, 0) AS category_diversity_count,
    
    -- Payment Behavior
    COALESCE(p.avg_payment_installments, 1.0) AS avg_installments,
    COALESCE(p.uses_credit_card, 0) AS is_credit_card_user,
    COALESCE(p.uses_upi, 0) AS is_upi_user,
    
    -- Satisfaction & Support Signals
    COALESCE(r.avg_csat_score, 3.5) AS avg_csat_score,
    COALESCE(r.low_rating_count, 0) AS negative_feedback_count,
    
    -- Target Variable: 1 if last purchase occurred BEFORE the 90-day cutoff, else 0
    CASE 
        WHEN DATE(b.last_order_date) <= s.churn_cutoff_date THEN 1 
        ELSE 0 
    END AS is_churned
FROM customer_base_metrics b
CROSS JOIN observation_snapshot s
LEFT JOIN customer_financial_metrics f ON b.customer_id = f.customer_id
LEFT JOIN customer_payment_metrics p ON b.customer_id = p.customer_id
LEFT JOIN customer_review_metrics r ON b.customer_id = r.customer_id
WHERE b.completed_orders > 0;
