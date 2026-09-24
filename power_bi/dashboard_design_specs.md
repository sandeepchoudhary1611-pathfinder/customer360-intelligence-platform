# Customer360 - Executive Power BI Dashboard Design Specifications

This specification guides the construction of a world-class, 3-page interactive Power BI dashboard designed for executive leadership (CCO, CMO, Head of Data).

---

## Global Design Standards & Design System
* **Canvas Size:** 16:9 widescreen (1920 x 1080 px or standard 1280 x 720 px).
* **Grid & Padding:** 8px base grid, 16px card padding, 12px border radius on containers.
* **Color Palette:**
  * **Primary Brand Navy:** `#0F172A` (Headers, sidebar, primary text)
  * **Accent Corporate Blue:** `#2563EB` (Primary series, active filters, trend lines)
  * **Critical Risk Crimson:** `#EF4444` (Churn alerts, negative variances)
  * **Warning Amber:** `#F59E0B` (Moderate risk, pending orders)
  * **Success Emerald:** `#10B981` (Retained customers, positive YoY growth)
  * **Neutral Background:** `#F8FAFC` (Canvas background)
  * **Card Container White:** `#FFFFFF` with light drop-shadow (`rgba(0,0,0,0.04)`)

---

## Page 1: Executive C-Suite Overview
**Goal:** High-level strategic monitoring of revenue, order volume, margins, and churn velocity.

### Layout Breakdown
```
+---------------------------------------------------------------------------------------------------+
|  HEADER: Customer360 Executive Intelligence Overview           [Filters: Year | Segment | Region] |
+---------------------------------------------------------------------------------------------------+
| [ KPI 1: Total Revenue ] [ KPI 2: Delivered Orders ] [ KPI 3: Gross Margin % ] [ KPI 4: Churn % ] |
|   INR 106.8M (+14% YoY)       24.7K Orders                 54.2% (+1.8 pts)          27.8% Critical |
+--------------------------------------------------+------------------------------------------------+
| Visual 1: Monthly Revenue & Order Volume Trend   | Visual 2: Revenue Contribution by Segment & Ch |
| (Line & Clustered Column Chart)                  | (Donut Chart / 100% Stacked Bar)              |
| X-axis: Month Year                               | Legend: Consumer vs SME vs Corporate           |
| Column: Total Revenue | Line: Order Count        | Values: Total Revenue                          |
+--------------------------------------------------+------------------------------------------------+
| Visual 3: Geographic Revenue Distribution        | Visual 4: Customer Satisfaction (CSAT) vs Vol  |
| (Filled Map or Horizontal Bar by State)          | (Scatter Plot: Avg CSAT vs Total Spend)        |
+---------------------------------------------------------------------------------------------------+
```

---

## Page 2: Customer Segmentation & Cohort Retention
**Goal:** Deep-dive into behavioral segments (RFM) and cohort repeat purchase stickiness.

### Layout Breakdown
```
+---------------------------------------------------------------------------------------------------+
|  HEADER: Customer Behavioral Segments & Retention Heatmap      [Slicer: Acquisition Channel]      |
+---------------------------------------------------------------------------------------------------+
| Visual 1: RFM Customer Segment Quadrant (Scatter Plot)                                            |
| X-axis: Recency (Days Inactive) | Y-axis: Frequency (Total Orders) | Bubble Size: Total Spend     |
| Color: Customer RFM Category (Champions, At Risk, Loyal, Promising)                                |
+--------------------------------------------------+------------------------------------------------+
| Visual 2: Product Category Performance Matrix    | Visual 3: Customer Lifetime Value (CLV)        |
| (Decomposition Tree or Clustered Bar)            | (Bar chart: Avg CLV by Customer Segment)      |
| Electronics > Fashion > Home > Health            | Consumer: INR 12.4K | SME: INR 28.5K           |
+--------------------------------------------------+------------------------------------------------+
| Visual 4: Monthly Cohort Retention Heatmap (Matrix Table)                                         |
| Rows: Cohort Month (2024-01, 2024-02...) | Columns: Month 0, Month 1, Month 2, Month 3...        |
| Values: [Cohort Retention %] with Conditional Formatting (Dark Blue to Pale White)                |
+---------------------------------------------------------------------------------------------------+
```

---

## Page 3: Predictive Churn Risk & AI Retention Center
**Goal:** Operational triage of at-risk revenue, high-probability churners, and targeted action plans.

### Layout Breakdown
```
+---------------------------------------------------------------------------------------------------+
|  HEADER: Predictive Churn Risk & AI Retention Center           [Slicer: Risk Tier Filter]         |
+---------------------------------------------------------------------------------------------------+
| [ KPI 1: Total Revenue at Risk ]  [ KPI 2: Critical Risk Accounts ]  [ KPI 3: Avg Churn Probability ]|
|         INR 43.8 Million                     2,149 Accounts                     58.4% Average      |
+--------------------------------------------------+------------------------------------------------+
| Visual 1: Churn Probability Distribution         | Visual 2: Top Drivers of Churn (ML Importance) |
| (Histogram / Binned Column Chart)                | (Horizontal Bar Chart)                         |
| Low (<40%) | Moderate (40-69%) | Critical (>=70%)| 1. Recency 2. CSAT Drop 3. Discount Sensitivity|
+--------------------------------------------------+------------------------------------------------+
| Visual 3: High-Priority At-Risk Accounts Table (Triage Grid)                                      |
| Columns: Customer ID | Segment | Lifetime Spend | Churn Prob % | Rev at Risk | CSAT | Action     |
| Conditional Formatting: Red badges for >=70% risk tier                                            |
| Tooltip: Hover to preview customer purchase history and AI recommended intervention                |
+---------------------------------------------------------------------------------------------------+
```

---

## Drill-Through Page: Customer 360 Profile (Target Modal)
When an executive right-clicks any customer row on Page 3:
* **Drill-Through Target:** `Customer 360 Profile`
* **Contents:**
  * Customer ID, City, State, Account Age, Acquisition Channel.
  * Historical timeline of all past orders and review ratings.
  * Direct AI prescriptive recommendation box (copied from Copilot report).
