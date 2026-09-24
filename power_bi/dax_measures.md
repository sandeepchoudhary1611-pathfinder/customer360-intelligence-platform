# Customer360 Intelligence Platform - Enterprise Power BI DAX Calculation Handbook
**Project:** Customer360 Intelligence & Predictive Churn Platform  
**Data Model:** Star Schema (1-to-Many Single Direction Relationships)  
**Tools:** Power BI Desktop / Service  

---

## 1. Core Foundational Measures (Base Aggregations)

### Total Revenue
```dax
Total Revenue = 
SUM(fact_order_items[total_amount])
```

### Total Delivered Orders
```dax
Total Orders = 
CALCULATE(
    DISTINCTCOUNT(fact_orders[order_id]),
    fact_orders[order_status] = "Delivered"
)
```

### Total Active Customers
```dax
Active Customers = 
CALCULATE(
    DISTINCTCOUNT(fact_orders[customer_id]),
    fact_orders[order_status] = "Delivered"
)
```

### Average Order Value (AOV)
```dax
Average Order Value = 
DIVIDE([Total Revenue], [Total Orders], 0)
```

### Gross Margin (INR & %)
```dax
Total COGS = 
SUMX(
    fact_order_items,
    fact_order_items[quantity] * RELATED(dim_products[unit_cost])
)

Gross Profit = 
[Total Revenue] - [Total COGS]

Gross Margin % = 
DIVIDE([Gross Profit], [Total Revenue], 0)
```

---

## 2. Customer Health & Churn Metrics

### Churned Customers Count
```dax
Churned Customers = 
CALCULATE(
    DISTINCTCOUNT(fact_customer_churn_scores[customer_id]),
    fact_customer_churn_scores[is_churned] = 1
)
```

### Portfolio Churn Rate %
```dax
Churn Rate % = 
DIVIDE([Churned Customers], DISTINCTCOUNT(dim_customers[customer_id]), 0)
```

### Revenue at Risk (INR)
```dax
Total Revenue at Risk = 
SUM(fact_customer_churn_scores[revenue_at_risk])
```

### Critical Risk Customers (>= 70% Probability)
```dax
Critical Risk Customers = 
CALCULATE(
    DISTINCTCOUNT(fact_customer_churn_scores[customer_id]),
    fact_customer_churn_scores[churn_probability] >= 0.70
)
```

### Average Churn Probability
```dax
Average Churn Probability = 
AVERAGE(fact_customer_churn_scores[churn_probability])
```

---

## 3. Time Intelligence Measures (MoM & YoY Performance)

### Prior Month Revenue (MoM)
```dax
Revenue Prior Month = 
CALCULATE(
    [Total Revenue],
    DATEADD(dim_date[Date], -1, MONTH)
)
```

### Month-over-Month Revenue Growth %
```dax
MoM Revenue Growth % = 
VAR _Current = [Total Revenue]
VAR _Prior = [Revenue Prior Month]
RETURN
DIVIDE(_Current - _Prior, _Prior, 0)
```

### Same Period Last Year (SPLY) Revenue
```dax
Revenue SPLY = 
CALCULATE(
    [Total Revenue],
    SAMEPERIODLASTYEAR(dim_date[Date])
)
```

### Year-over-Year Revenue Growth %
```dax
YoY Revenue Growth % = 
VAR _Current = [Total Revenue]
VAR _Prior = [Revenue SPLY]
RETURN
DIVIDE(_Current - _Prior, _Prior, 0)
```

---

## 4. Cohort Retention DAX (Triangular Matrix Analysis)

### Customer First Purchase Date (Calculated Column in `dim_customers`)
```dax
First Purchase Date = 
CALCULATE(
    MIN(fact_orders[order_purchase_timestamp]),
    ALLEXCEPT(dim_customers, dim_customers[customer_id]),
    fact_orders[order_status] = "Delivered"
)
```

### Cohort Month (Calculated Column in `dim_customers`)
```dax
Cohort Month = 
FORMAT(dim_customers[First Purchase Date], "YYYY-MM")
```

### Cohort Month Number (Period Offset)
```dax
Cohort Month Index = 
VAR _CohortDate = dim_customers[First Purchase Date]
VAR _OrderDate = SELECTEDVALUE(fact_orders[order_purchase_timestamp])
RETURN
IF(
    NOT(ISBLANK(_OrderDate)),
    (YEAR(_OrderDate) - YEAR(_CohortDate)) * 12 + (MONTH(_OrderDate) - MONTH(_CohortDate)),
    BLANK()
)
```

### Cohort Retention % (Matrix Measure)
```dax
Cohort Retention % = 
VAR _BaseCohortCustomers = 
    CALCULATE(
        [Active Customers],
        ALLEXCEPT(dim_customers, dim_customers[Cohort Month])
    )
VAR _ActiveInPeriod = [Active Customers]
RETURN
DIVIDE(_ActiveInPeriod, _BaseCohortCustomers, 0)
```

---

## 5. Advanced UI & Dynamic Parameter Measures

### Dynamic KPI Switcher (Supports Parameterized Charts)
*Created with a disconnected parameter table `Metric_Selection[Metric_Name]`*
```dax
Selected KPI Value = 
SWITCH(
    SELECTEDVALUE(Metric_Selection[Metric_Name], "Total Revenue"),
    "Total Revenue", [Total Revenue],
    "Delivered Orders", [Total Orders],
    "Active Customers", [Active Customers],
    "Gross Margin %", [Gross Margin %],
    "Revenue at Risk", [Total Revenue at Risk],
    [Total Revenue]
)
```

### Dynamic Card Title
```dax
Dynamic Chart Title = 
"Monthly Trend Analysis: " & SELECTEDVALUE(Metric_Selection[Metric_Name], "Total Revenue")
```

### Churn Risk Status Indicator (Color Formatting)
```dax
Risk Status Hex Color = 
SWITCH(
    SELECTEDVALUE(fact_customer_churn_scores[churn_risk_tier]),
    "Critical Risk (>=70%)", "#E63946",   -- Crimson Red
    "Moderate Risk (40-69%)", "#F4A261",  -- Amber Orange
    "Low Risk (<40%)", "#2A9D8F",         -- Emerald Green
    "#264653"                             -- Slate Blue Default
)
```
