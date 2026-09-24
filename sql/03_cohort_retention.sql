-- ============================================================================
-- Customer360: Monthly Customer Cohort Retention Analysis (Triangular Matrix)
-- Dialect: ANSI SQL / Compatible with SQLite, PostgreSQL, DuckDB
-- ============================================================================
-- Business Objective:
-- Determine customer stickiness and repeat-purchase behavior over time.
-- 1. Identify each customer's first purchase month (Cohort Month).
-- 2. Track customer activity in subsequent months.
-- 3. Calculate period index (Month 0, Month 1, Month 2, ... Month 12).
-- 4. Compute retention percentage relative to Cohort Size (Month 0).
-- ============================================================================

WITH customer_first_purchase AS (
    -- Step 1: Pinpoint the Cohort Month (first ever delivered purchase)
    SELECT 
        customer_id,
        MIN(STRFTIME('%Y-%m', order_purchase_timestamp)) AS cohort_month
    FROM fact_orders
    WHERE order_status = 'Delivered'
    GROUP BY customer_id
),

customer_monthly_activity AS (
    -- Step 2: Extract all distinct active purchase months per customer
    SELECT DISTINCT
        o.customer_id,
        STRFTIME('%Y-%m', o.order_purchase_timestamp) AS activity_month
    FROM fact_orders o
    WHERE o.order_status = 'Delivered'
),

cohort_activity AS (
    -- Step 3: Join cohort definitions with monthly activities and calculate period offset
    SELECT 
        c.cohort_month,
        a.activity_month,
        -- Calculate the month offset between activity month and cohort month
        (
            (CAST(SUBSTR(a.activity_month, 1, 4) AS INT) - CAST(SUBSTR(c.cohort_month, 1, 4) AS INT)) * 12 +
            (CAST(SUBSTR(a.activity_month, 6, 2) AS INT) - CAST(SUBSTR(c.cohort_month, 6, 2) AS INT))
        ) AS cohort_period_index,
        COUNT(DISTINCT a.customer_id) AS active_customers
    FROM customer_first_purchase c
    INNER JOIN customer_monthly_activity a ON c.customer_id = a.customer_id
    GROUP BY c.cohort_month, a.activity_month
),

cohort_base_sizes AS (
    -- Step 4: Extract Month 0 base size per cohort
    SELECT 
        cohort_month,
        active_customers AS initial_cohort_size
    FROM cohort_activity
    WHERE cohort_period_index = 0
)

-- Step 5: Produce the final Cohort Retention Grid with percentages
SELECT 
    ca.cohort_month,
    cb.initial_cohort_size,
    ca.cohort_period_index AS month_number,
    ca.active_customers,
    ROUND((ca.active_customers * 100.0) / cb.initial_cohort_size, 2) AS retention_rate_pct
FROM cohort_activity ca
INNER JOIN cohort_base_sizes cb ON ca.cohort_month = cb.cohort_month
ORDER BY ca.cohort_month ASC, ca.cohort_period_index ASC;
