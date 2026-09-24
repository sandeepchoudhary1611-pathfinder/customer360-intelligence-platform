# Customer360 - Power BI Data Model Architecture & Schema Design

## 1. Star Schema Architecture

The data model follows an enterprise Star Schema to optimize DAX query performance, eliminate bidirectional relationship ambiguity, and ensure clean filter propagation.

```
       +--------------------+          +--------------------+
       |   dim_customers    |          |    dim_products    |
       +--------------------+          +--------------------+
       | PK customer_id     |          | PK product_id      |
       +---------+----------+          +---------+----------+
                 | 1                             | 1
                 |                               |
                 | *                             | *
       +---------v----------+          +---------v----------+
       |    fact_orders     |<---+ *   | fact_order_items   |
       +--------------------+    |     +--------------------+
       | PK order_id        |    |     | PK order_item_id   |
       | FK customer_id     |    +-----+ FK order_id        |
       | order_purchase_ts  |          | FK product_id      |
       +---------+----------+          | quantity, price    |
                 | 1                   +--------------------+
                 |
                 +-------------------+
                 | *                 | *
       +---------v----------+  +-----v--------------+
       |   fact_payments    |  |fact_customer_review|
       +--------------------+  +--------------------+
       | PK payment_id      |  | PK review_id       |
       | FK order_id        |  | FK order_id        |
       +--------------------+  +--------------------+

                 ^
                 | 1:1 / 1:*
       +---------+--------------------+
       |  fact_customer_churn_scores  |  <--- Output of Scikit-Learn Pipeline
       +------------------------------+
       | FK customer_id               |
       | churn_probability, risk_tier |
       | revenue_at_risk              |
       +------------------------------+
```

---

## 2. Table Relationships & Cardinality Configuration

| From Table (Fact / Child) | Foreign Key | To Table (Dimension / Parent) | Primary Key | Cardinality | Cross Filter Direction |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `fact_orders` | `customer_id` | `dim_customers` | `customer_id` | Many-to-One (*:1) | Single (`dim_customers` filters `fact_orders`) |
| `fact_order_items` | `order_id` | `fact_orders` | `order_id` | Many-to-One (*:1) | Single (`fact_orders` filters `fact_order_items`) |
| `fact_order_items` | `product_id` | `dim_products` | `product_id` | Many-to-One (*:1) | Single (`dim_products` filters `fact_order_items`) |
| `fact_payments` | `order_id` | `fact_orders` | `order_id` | Many-to-One (*:1) | Single (`fact_orders` filters `fact_payments`) |
| `fact_customer_reviews` | `order_id` | `fact_orders` | `order_id` | Many-to-One (*:1) | Single (`fact_orders` filters `fact_customer_reviews`) |
| `fact_customer_churn_scores` | `customer_id` | `dim_customers` | `customer_id` | Many-to-One (*:1) | Single (`dim_customers` filters churn scores) |
| `fact_orders` | `order_purchase_timestamp` | `dim_date` | `Date` | Many-to-One (*:1) | Single (`dim_date` filters `fact_orders`) |

> **Best Practice Rule:** Never enable Bi-directional (`Both`) cross-filtering unless strictly required for a Many-to-Many bridge. Single-direction filtering prevents circular dependency deadlocks and optimizes the VertiPaq engine cache.

---

## 3. Dedicated Date Dimension DAX Table (`dim_date`)

Create a calculated table in Power BI to enable robust Time-Intelligence:

```dax
dim_date = 
VAR _MinDate = DATE(2024, 1, 1)
VAR _MaxDate = DATE(2026, 12, 31)
RETURN
ADDCOLUMNS(
    CALENDAR(_MinDate, _MaxDate),
    "Year", YEAR([Date]),
    "Quarter", "Q" & FORMAT([Date], "Q"),
    "Month Number", MONTH([Date]),
    "Month Name", FORMAT([Date], "MMM"),
    "Month Year", FORMAT([Date], "MMM YYYY"),
    "Month Year Order", YEAR([Date]) * 100 + MONTH([Date]),
    "Day of Week", FORMAT([Date], "ddd"),
    "Day Number of Week", WEEKDAY([Date], 2),
    "Is Weekend", IF(WEEKDAY([Date], 2) >= 6, "Weekend", "Weekday")
)
```
*Note: Ensure `Month Name` is sorted by `Month Number`, and `Month Year` is sorted by `Month Year Order` in Power BI Column Tools.*
