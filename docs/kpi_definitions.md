# Banking Loan Risk Analysis - KPI Definitions

## Purpose

This document defines the business and analytical KPIs used in the Banking Loan Risk Analysis application.

The KPIs are calculated from the curated MySQL database and are used by the SQL analytics layer, REST API, and Streamlit dashboard.

---

## Portfolio KPIs

### K1 - Total Customers
**Definition:** Total number of unique customers in the portfolio.

**Purpose:** Measures the overall size of the customer portfolio.

**Source:** `customers.customer_id`

---

### K2 - Total Credit Exposure
**Definition:** Sum of credit limits assigned to all customers.

**Formula:**

Total Credit Exposure = SUM(credit_limit)

**Source:** `credit_profiles.credit_limit`

---

### K3 - Average Credit Limit
**Definition:** Average credit limit assigned per customer.

**Formula:**

Average Credit Limit = AVG(credit_limit)

**Source:** `credit_profiles.credit_limit`

---

### K4 - Historical Default Rate
**Definition:** Percentage of customers whose historical target indicates default in the following month.

**Formula:**

Historical Default Rate =
(Default Customers / Total Customers) * 100

**Source:** `credit_profiles.default_next_month`

**Note:** This is an observed historical outcome and is not the application's rule-based risk classification.

---

### K5 - Customers With Payment Delay
**Definition:** Number of customers having at least one month with a positive repayment delay status.

**Source:** `credit_profiles.has_payment_delay`

---

### K6 - Repeated Delay Rate
**Definition:** Percentage of customers with positive repayment delays in two or more of the six observed months.

**Formula:**

Repeated Delay Rate =
(Customers with delay_month_count >= 2 / Total Customers) * 100

**Source:** `credit_profiles.delay_month_count`

---

### K7 - Average Latest Utilization
**Definition:** Average latest bill amount relative to the customer's credit limit.

**Formula:**

Latest Utilization =
Latest Bill Amount / Credit Limit

**Source:** `credit_profiles.latest_utilization_ratio`

---

### K8 - Over-Limit Customers
**Definition:** Number of customers whose latest bill amount exceeds their assigned credit limit.

**Condition:**

latest_utilization_ratio > 1

**Source:** `credit_profiles.latest_utilization_ratio`

---

### K9 - Total 6-Month Bill Amount
**Definition:** Total billed amount across the six-month observation period for all customers.

**Source:** `credit_profiles.total_bill_amount_6m`

---

### K10 - Total 6-Month Payment Amount
**Definition:** Total payment amount across the six-month observation period for all customers.

**Source:** `credit_profiles.total_payment_amount_6m`

---

## Customer Segment Analytics

KPIs will also be analyzed across:

- Gender
- Education
- Marital status
- Age groups

Segment analysis will include customer count, average credit limit, historical default rate, repayment delays, and utilization.

---

## Repayment Behaviour Analytics

Repayment behaviour will be analyzed using:

- `delay_month_count`
- `max_delay_status`
- `has_payment_delay`

Historical default rates will be compared across repayment-delay groups.

---

## Monthly Trend Analytics

Monthly analysis will use `monthly_credit_activity` to calculate:

- Total bill amount
- Total payment amount
- Average bill amount
- Average payment amount
- Number of customers with positive repayment delays

The available observation period is April 2005 through September 2005.

---

## Risk Classification Note

The dataset field `default_next_month` represents the historical observed default outcome.

It must not be directly used as the application's Low / Medium / High risk classification.

The application's risk bands will be calculated separately using documented and transparent business rules based on customer repayment and credit behaviour.