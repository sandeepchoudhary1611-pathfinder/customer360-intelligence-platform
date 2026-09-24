-- ============================================================================
-- Customer360: Customer Lifetime Value (CLV) & Purchase Velocity Analysis
-- Dialect: ANSI SQL / Compatible with SQLite, PostgreSQL, DuckDB
-- ============================================================================
-- Business Objective:
-- Measure unit economics per customer:
-- 1. Total historical revenue and gross profit contribution
-- 2. Average Order Value (AOV) and purchase frequency
-- 3. Repeat purchase velocity: Days between consecutive orders using LAG()
-- 4. Customer Lifespan: Days from first order to last order
-- ============================================================================

WITH order_level_financials AS (
    -- Calculate gross revenue, cost of goods sold (COGS), and gross margin per order
    SELECT 
        o.order_id,
        o.customer_id,
        o.order_purchase_timestamp,
        SUM(oi.total_amount) AS order_revenue,
        SUM(p.unit_cost * oi.quantity) AS order_cogs,
        SUM(oi.discount_amount) AS total_discount,
        SUM(oi.total_amount - (p.unit_cost * oi.quantity)) AS gross_profit
    FROM fact_orders o
    INNER JOIN fact_order_items oi ON o.order_id = oi.order_id
    INNER JOIN dim_products p ON oi.product_id = p.product_id
    WHERE o.order_status = 'Delivered'
    GROUP BY o.order_id, o.customer_id, o.order_purchase_timestamp
),

order_intervals AS (
    -- Use LAG() window function to compute time elapsed between consecutive orders
    SELECT 
        order_id,
        customer_id,
        order_purchase_timestamp,
        order_revenue,
        gross_profit,
        LAG(order_purchase_timestamp, 1) OVER (
            PARTITION BY customer_id 
            ORDER BY order_purchase_timestamp ASC
        ) AS previous_order_timestamp
    FROM order_level_financials
),

customer_velocities AS (
    -- Calculate inter-purchase intervals in days
    SELECT 
        customer_id,
        order_id,
        order_revenue,
        gross_profit,
        CASE 
            WHEN previous_order_timestamp IS NOT NULL THEN 
                CAST(JULIANDAY(order_purchase_timestamp) - JULIANDAY(previous_order_timestamp) AS INT)
            ELSE NULL 
        END AS days_since_prior_order
    FROM order_intervals
)

-- Final Customer Lifetime Value Summary
SELECT 
    c.customer_id,
    c.customer_segment,
    c.acquisition_channel,
    c.customer_state,
    COUNT(DISTINCT cv.order_id) AS lifetime_orders,
    ROUND(SUM(cv.order_revenue), 2) AS historical_clv_revenue,
    ROUND(SUM(cv.gross_profit), 2) AS historical_gross_profit,
    ROUND(AVG(cv.order_revenue), 2) AS average_order_value,
    ROUND(
        CASE 
            WHEN SUM(cv.order_revenue) > 0 
            THEN (SUM(cv.gross_profit) * 100.0) / SUM(cv.order_revenue)
            ELSE 0 
        END, 2
    ) AS gross_margin_pct,
    ROUND(AVG(cv.days_since_prior_order), 1) AS avg_days_between_purchases,
    MIN(o.order_purchase_timestamp) AS first_order_date,
    MAX(o.order_purchase_timestamp) AS latest_order_date,
    CAST(
        JULIANDAY(MAX(o.order_purchase_timestamp)) - JULIANDAY(MIN(o.order_purchase_timestamp)) AS INT
    ) AS customer_active_lifespan_days
FROM dim_customers c
INNER JOIN customer_velocities cv ON c.customer_id = cv.customer_id
INNER JOIN fact_orders o ON cv.order_id = o.order_id
GROUP BY c.customer_id, c.customer_segment, c.acquisition_channel, c.customer_state
ORDER BY historical_clv_revenue DESC;
