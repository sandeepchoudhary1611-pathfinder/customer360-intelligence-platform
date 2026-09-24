-- ============================================================================
-- Customer360: RFM (Recency, Frequency, Monetary) Customer Segmentation
-- Dialect: ANSI SQL / Compatible with SQLite, PostgreSQL, DuckDB
-- ============================================================================
-- Business Objective:
-- Quantify customer behavioral value by calculating:
-- 1. Recency: Days since last completed purchase (relative to snapshot date)
-- 2. Frequency: Total number of completed orders
-- 3. Monetary: Total revenue generated across all completed orders
-- Then rank customers into quintiles (1-5) using NTILE window functions and
-- assign human-interpretable marketing segments (e.g. Champions, At Risk).
-- ============================================================================

WITH analysis_boundary AS (
    -- Dynamically establish the reference date (max order timestamp + 1 day)
    SELECT DATE(MAX(order_purchase_timestamp), '+1 day') AS snapshot_date
    FROM fact_orders
    WHERE order_status = 'Delivered'
),

customer_aggregates AS (
    -- Aggregate raw customer activity
    SELECT 
        c.customer_id,
        c.customer_unique_id,
        c.customer_segment,
        c.acquisition_channel,
        c.customer_state,
        COUNT(DISTINCT o.order_id) AS total_orders,
        MAX(o.order_purchase_timestamp) AS last_order_date,
        SUM(oi.total_amount) AS total_spend,
        AVG(oi.total_amount) AS average_order_value,
        AVG(r.review_score) AS avg_review_score,
        -- Calculate recency in days relative to snapshot
        CAST(
            JULIANDAY((SELECT snapshot_date FROM analysis_boundary)) - 
            JULIANDAY(MAX(o.order_purchase_timestamp)) AS INT
        ) AS recency_days
    FROM dim_customers c
    INNER JOIN fact_orders o ON c.customer_id = o.customer_id
    INNER JOIN fact_order_items oi ON o.order_id = oi.order_id
    LEFT JOIN fact_customer_reviews r ON o.order_id = r.order_id
    WHERE o.order_status = 'Delivered'
    GROUP BY 
        c.customer_id, 
        c.customer_unique_id, 
        c.customer_segment, 
        c.acquisition_channel, 
        c.customer_state
),

rfm_quantiles AS (
    -- Window function: Divide customers into 5 score bins (1 = Lowest, 5 = Highest)
    -- For Recency: Lower days = Better (So rank descending to assign 5 to lowest days)
    SELECT 
        customer_id,
        customer_unique_id,
        customer_segment,
        acquisition_channel,
        customer_state,
        recency_days,
        total_orders,
        total_spend,
        average_order_value,
        avg_review_score,
        NTILE(5) OVER (ORDER BY recency_days DESC) AS r_score,
        NTILE(5) OVER (ORDER BY total_orders ASC) AS f_score,
        NTILE(5) OVER (ORDER BY total_spend ASC) AS m_score
    FROM customer_aggregates
),

rfm_scoring AS (
    SELECT 
        *,
        (r_score * 100 + f_score * 10 + m_score) AS rfm_combined_code,
        ROUND((r_score + f_score + m_score) / 3.0, 2) AS rfm_composite_index
    FROM rfm_quantiles
)

-- Final Segment Assignment with Actionable Business Logic
SELECT 
    customer_id,
    customer_unique_id,
    customer_segment,
    acquisition_channel,
    customer_state,
    recency_days,
    total_orders,
    total_spend,
    average_order_value,
    avg_review_score,
    r_score,
    f_score,
    m_score,
    rfm_combined_code,
    rfm_composite_index,
    CASE 
        WHEN r_score >= 4 AND f_score >= 4 AND m_score >= 4 THEN 'Champions'
        WHEN r_score >= 3 AND f_score >= 3 AND m_score >= 3 THEN 'Loyal Customers'
        WHEN r_score >= 4 AND f_score <= 2 THEN 'Promising / New Customers'
        WHEN r_score <= 2 AND f_score >= 4 AND m_score >= 4 THEN 'Can’t Lose Them (Critical Risk)'
        WHEN r_score <= 2 AND f_score >= 3 THEN 'At Risk (High Value Inactive)'
        WHEN r_score = 3 AND f_score <= 2 THEN 'Needs Attention'
        WHEN r_score <= 2 AND f_score <= 2 AND m_score >= 3 THEN 'Sleeping Spenders'
        ELSE 'Hibernating / Low Value Churned'
    END AS customer_rfm_segment
FROM rfm_scoring
ORDER BY total_spend DESC;
