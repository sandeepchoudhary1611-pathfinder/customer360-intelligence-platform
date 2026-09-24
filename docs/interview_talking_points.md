# Customer360: Interview Defense & Technical Talking Points

This document provides exact framing, answers, and technical rationale for interviewers (Data Leads, Analytics Directors, Engineering Managers, and HR).

---

## 1. The Opening Pitch (Framing the UPSC Gap & IIT Delhi Background)

### Question: "Tell me about yourself. You graduated from IIT Delhi in 2024—what have you been working on?"

**Model Response:**
> *"I graduated from IIT Delhi in 2024 with a degree in Chemical Engineering, where I developed strong mathematical modeling and analytical problem-solving foundations. Following graduation, I spent time rigorously preparing for the UPSC Civil Services Examination. That journey was invaluable—it sharpened my structured thinking, macro-economic comprehension, and mental resilience under ambiguity.*
> 
> *However, my primary passion lies in data analytics and applied technology. I made a conscious, deliberate pivot to the corporate analytics sector, backing up my engineering foundation with production-grade proof of work. Over the past several months, I have built complete end-to-end data systems—spanning ANSI SQL database modeling, predictive machine learning pipelines in Python, enterprise Power BI dashboards with complex DAX, and Generative AI copilots.*
> 
> *For example, in my recent Customer360 project, I architected a full customer intelligence and churn prediction platform that identified INR 43.8 Million in revenue exposure and formulated automated AI retention playbooks. I am looking forward to bringing this mix of analytical rigor and technical execution to your team."*

---

## 2. Technical Deep-Dive: Advanced SQL

### Question: "How did you implement cohort retention analysis in SQL? Can you explain the logic?"

**Model Response:**
> *"Cohort analysis requires measuring customer stickiness over monthly intervals. I structured it using Common Table Expressions (CTEs):*
> 1. *First, I determined each customer's `cohort_month` using `MIN(order_purchase_timestamp)` grouped by `customer_id`.*
> 2. *Second, I extracted distinct monthly activity periods for each customer.*
> 3. *Third, I computed the relative period offset index (`month_number`) by calculating `(activity_year - cohort_year) * 12 + (activity_month - cohort_month)`.*
> 4. *Fourth, I joined the baseline Month 0 cohort size back to subsequent periods and computed the percentage: `(active_customers_in_period * 100.0) / initial_cohort_size`.*
> 
> *This produces a triangular retention matrix that directly reveals if customer repeat rates stabilize after Month 3, which is critical for forecasting Customer Lifetime Value (CLV)."*

### Question: "Why did you use `NTILE(5)` and `LAG()` in your SQL scripts?"

**Model Response:**
> *"In the RFM segmentation script, `NTILE(5) OVER (ORDER BY recency_days DESC)` partitions customers into 5 equal quintiles based on their recency, frequency, and monetary spend, creating normalized 1–5 scores.*
> 
> *In the CLV script, I used `LAG(order_purchase_timestamp) OVER (PARTITION BY customer_id ORDER BY order_purchase_timestamp)` to pull the timestamp of a customer's prior transaction into the current row. This enabled me to calculate the exact inter-purchase velocity (days between consecutive orders). If this interval starts widening, it serves as an early leading indicator of churn before the customer becomes completely inactive."*

---

## 3. Technical Deep-Dive: Python & Machine Learning

### Question: "What was your modeling strategy for predicting customer churn? Did you encounter target leakage?"

**Model Response:**
> *"Yes, and identifying that leakage was a key engineering milestone. In churn modeling, the business label is often defined by a cutoff—for example, 'no order in the last 90 days'. If you inadvertently feed `recency_days` into the model, the classifier achieves a misleading 100% ROC-AUC because it simply memorizes `if recency >= 90 then 1`.*
> 
> *To prevent deterministic target leakage, I explicitly decoupled the observation window from the prediction window. I removed raw recency from the feature matrix and forced the model to learn from pure behavioral signals: drop in customer review ratings (CSAT), discount price sensitivity, order frequency velocity, basket diversity, and failed order rates.*
> 
> *Using Scikit-learn's `ColumnTransformer` and `Pipeline`, I benchmarked Logistic Regression against a Random Forest classifier (150 trees). Random Forest achieved a realistic, robust test ROC-AUC of 0.7040 and F1-score of 0.7182. More importantly, I computed Brier score loss to ensure calibrated probability outputs, which directly fed into our financial 'Revenue at Risk' calculation."*

---

## 4. Technical Deep-Dive: Power BI & Data Modeling

### Question: "How did you design the Power BI data model? Why avoid bidirectional cross-filtering?"

**Model Response:**
> *"I built a strict Star Schema centered around transactional fact tables (`fact_orders`, `fact_order_items`, `fact_payments`, `fact_customer_reviews`, and `fact_customer_churn_scores`) surrounded by dimension tables (`dim_customers`, `dim_products`, and a DAX-generated `dim_date`).*
> 
> *All relationships are 1-to-Many with single-direction filtering from dimensions down to facts. I strictly avoid bidirectional filtering because:*
> 1. *It can create circular filter propagation and ambiguous calculation paths.*
> 2. *It bypasses the high-performance column-oriented optimizations of the VertiPaq engine, degrading performance on large transactional volumes.*
> 
> *For complex interactions, I handle filter context explicitly in DAX using `CALCULATE`, `FILTER`, `ALL`, and `ALLEXCEPT`."*

### Question: "How do dynamic measures work in your dashboard?"

**Model Response:**
> *"To prevent cluttering the executive view with 5 separate charts for Revenue, Orders, Margin, and Churn, I created a disconnected parameter table containing metric names. In DAX, I wrote a `SWITCH(SELECTEDVALUE(Metric_Selection[Metric_Name]), ...)` measure. When an executive selects a KPI from a slicer, the chart visual dynamically recalculates and re-renders without reloading the report."*

---

## 5. Technical Deep-Dive: Generative AI & Business Strategy

### Question: "Why did you add a GenAI component? Isn't an ML churn score enough?"

**Model Response:**
> *"In a real enterprise, machine learning models output a probability score (e.g., Customer #7440 has a 70.3% churn probability). But a CMO or Customer Success manager cannot directly take action on a decimal number.*
> 
> *There is a critical translation gap between predictive scores and business execution. By integrating the Gemini API, I built an automated retention copilot that pulls the high-risk customer profile (spend, recent low CSAT rating, preferred product category, days inactive) and formulates an actionable, unit-economic retention memo: recommending the exact outreach channel, personalized discount incentive, and projected win-back ROI.*
> 
> *It turns raw data analytics into prescriptive operational decisions."*
