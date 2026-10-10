-- ============================================================
-- BANKING LOAN RISK ANALYSIS
-- ANALYTICS AND KPI QUERIES
-- ============================================================

USE banking_loan_db;


-- ============================================================
-- K1 - TOTAL CUSTOMERS
-- ============================================================

SELECT
    COUNT(*) AS total_customers
FROM customers;


-- ============================================================
-- K2 - TOTAL CREDIT EXPOSURE
-- ============================================================

SELECT
    SUM(credit_limit) AS total_credit_exposure
FROM credit_profiles;


-- ============================================================
-- K3 - AVERAGE CREDIT LIMIT
-- ============================================================

SELECT
    ROUND(AVG(credit_limit), 2) AS average_credit_limit
FROM credit_profiles;


-- ============================================================
-- K4 - HISTORICAL DEFAULT RATE
-- ============================================================

SELECT
    COUNT(*) AS total_customers,

    SUM(
        CASE
            WHEN default_next_month = 1 THEN 1
            ELSE 0
        END
    ) AS default_customers,

    ROUND(
        100.0 *
        SUM(
            CASE
                WHEN default_next_month = 1 THEN 1
                ELSE 0
            END
        ) / COUNT(*),
        2
    ) AS historical_default_rate_pct

FROM credit_profiles;


-- ============================================================
-- K5 - CUSTOMERS WITH PAYMENT DELAY
-- ============================================================

SELECT
    SUM(
        CASE
            WHEN has_payment_delay = 1 THEN 1
            ELSE 0
        END
    ) AS customers_with_payment_delay
FROM credit_profiles;


-- ============================================================
-- K6 - REPEATED DELAY RATE
-- ============================================================

SELECT
    COUNT(*) AS total_customers,

    SUM(
        CASE
            WHEN delay_month_count >= 2 THEN 1
            ELSE 0
        END
    ) AS customers_with_repeated_delay,

    ROUND(
        100.0 *
        SUM(
            CASE
                WHEN delay_month_count >= 2 THEN 1
                ELSE 0
            END
        ) / COUNT(*),
        2
    ) AS repeated_delay_rate_pct

FROM credit_profiles;


-- ============================================================
-- K7 - AVERAGE LATEST UTILIZATION
-- ============================================================

SELECT
    ROUND(
        AVG(latest_utilization_ratio) * 100,
        2
    ) AS average_latest_utilization_pct
FROM credit_profiles;


-- ============================================================
-- K8 - OVER-LIMIT CUSTOMERS
-- ============================================================

SELECT
    SUM(
        CASE
            WHEN latest_utilization_ratio > 1 THEN 1
            ELSE 0
        END
    ) AS over_limit_customers,

    ROUND(
        100.0 *
        SUM(
            CASE
                WHEN latest_utilization_ratio > 1 THEN 1
                ELSE 0
            END
        ) / COUNT(*),
        2
    ) AS over_limit_customer_pct

FROM credit_profiles;


-- ============================================================
-- K9 - TOTAL 6-MONTH BILL AMOUNT
-- ============================================================

SELECT
    SUM(total_bill_amount_6m) AS total_bill_amount_6m
FROM credit_profiles;


-- ============================================================
-- K10 - TOTAL 6-MONTH PAYMENT AMOUNT
-- ============================================================

SELECT
    SUM(total_payment_amount_6m) AS total_payment_amount_6m
FROM credit_profiles;



-- ============================================================
-- PORTFOLIO KPI SUMMARY
-- ============================================================

SELECT
    COUNT(*) AS total_customers,

    SUM(credit_limit) AS total_credit_exposure,

    ROUND(
        AVG(credit_limit),
        2
    ) AS average_credit_limit,

    SUM(default_next_month) AS default_customers,

    ROUND(
        AVG(default_next_month) * 100,
        2
    ) AS historical_default_rate_pct,

    SUM(has_payment_delay) AS customers_with_payment_delay,

    SUM(
        CASE
            WHEN delay_month_count >= 2 THEN 1
            ELSE 0
        END
    ) AS customers_with_repeated_delay,

    ROUND(
        100.0 *
        SUM(
            CASE
                WHEN delay_month_count >= 2 THEN 1
                ELSE 0
            END
        ) / COUNT(*),
        2
    ) AS repeated_delay_rate_pct,

    ROUND(
        AVG(latest_utilization_ratio) * 100,
        2
    ) AS average_latest_utilization_pct,

    SUM(
        CASE
            WHEN latest_utilization_ratio > 1 THEN 1
            ELSE 0
        END
    ) AS over_limit_customers,

    SUM(total_bill_amount_6m)
        AS total_bill_amount_6m,

    SUM(total_payment_amount_6m)
        AS total_payment_amount_6m

FROM credit_profiles;




-- ============================================================
-- PHASE 4C - CUSTOMER SEGMENT ANALYTICS
-- ============================================================


-- ============================================================
-- SEGMENT 1 - GENDER
-- ============================================================

SELECT
    g.gender_name,

    COUNT(*) AS total_customers,

    ROUND(
        AVG(cp.credit_limit),
        2
    ) AS average_credit_limit,

    SUM(cp.default_next_month)
        AS default_customers,

    ROUND(
        AVG(cp.default_next_month) * 100,
        2
    ) AS historical_default_rate_pct,

    SUM(cp.has_payment_delay)
        AS customers_with_payment_delay,

    ROUND(
        AVG(cp.latest_utilization_ratio) * 100,
        2
    ) AS average_latest_utilization_pct

FROM customers c

INNER JOIN dim_gender g
    ON c.gender_code = g.gender_code

INNER JOIN credit_profiles cp
    ON c.customer_id = cp.customer_id

GROUP BY
    g.gender_code,
    g.gender_name

ORDER BY
    historical_default_rate_pct DESC;


-- ============================================================
-- SEGMENT 2 - EDUCATION
-- ============================================================

SELECT
    e.education_name,

    COUNT(*) AS total_customers,

    ROUND(
        AVG(cp.credit_limit),
        2
    ) AS average_credit_limit,

    SUM(cp.default_next_month)
        AS default_customers,

    ROUND(
        AVG(cp.default_next_month) * 100,
        2
    ) AS historical_default_rate_pct,

    SUM(cp.has_payment_delay)
        AS customers_with_payment_delay,

    ROUND(
        AVG(cp.latest_utilization_ratio) * 100,
        2
    ) AS average_latest_utilization_pct

FROM customers c

INNER JOIN dim_education e
    ON c.education_code = e.education_code

INNER JOIN credit_profiles cp
    ON c.customer_id = cp.customer_id

GROUP BY
    e.education_name

ORDER BY
    historical_default_rate_pct DESC;


-- ============================================================
-- SEGMENT 3 - MARITAL STATUS
-- ============================================================

SELECT
    m.marital_status_name,

    COUNT(*) AS total_customers,

    ROUND(
        AVG(cp.credit_limit),
        2
    ) AS average_credit_limit,

    SUM(cp.default_next_month)
        AS default_customers,

    ROUND(
        AVG(cp.default_next_month) * 100,
        2
    ) AS historical_default_rate_pct,

    SUM(cp.has_payment_delay)
        AS customers_with_payment_delay,

    ROUND(
        AVG(cp.latest_utilization_ratio) * 100,
        2
    ) AS average_latest_utilization_pct

FROM customers c

INNER JOIN dim_marital_status m
    ON c.marital_status_code = m.marital_status_code

INNER JOIN credit_profiles cp
    ON c.customer_id = cp.customer_id

GROUP BY
    m.marital_status_name

ORDER BY
    historical_default_rate_pct DESC;




-- ============================================================
-- SEGMENT 4 - AGE GROUP
-- ============================================================

SELECT
    CASE
        WHEN c.age BETWEEN 21 AND 29 THEN '21-29'
        WHEN c.age BETWEEN 30 AND 39 THEN '30-39'
        WHEN c.age BETWEEN 40 AND 49 THEN '40-49'
        WHEN c.age BETWEEN 50 AND 59 THEN '50-59'
        ELSE '60+'
    END AS age_group,

    COUNT(*) AS total_customers,

    ROUND(
        AVG(cp.credit_limit),
        2
    ) AS average_credit_limit,

    SUM(cp.default_next_month)
        AS default_customers,

    ROUND(
        AVG(cp.default_next_month) * 100,
        2
    ) AS historical_default_rate_pct,

    SUM(cp.has_payment_delay)
        AS customers_with_payment_delay,

    ROUND(
        AVG(cp.latest_utilization_ratio) * 100,
        2
    ) AS average_latest_utilization_pct

FROM customers c

INNER JOIN credit_profiles cp
    ON c.customer_id = cp.customer_id

GROUP BY
    CASE
        WHEN c.age BETWEEN 21 AND 29 THEN '21-29'
        WHEN c.age BETWEEN 30 AND 39 THEN '30-39'
        WHEN c.age BETWEEN 40 AND 49 THEN '40-49'
        WHEN c.age BETWEEN 50 AND 59 THEN '50-59'
        ELSE '60+'
    END

ORDER BY
    MIN(c.age);



-- ============================================================
-- PHASE 4D - REPAYMENT BEHAVIOUR ANALYTICS
-- ============================================================


-- ============================================================
-- D1 - DELAY MONTH COUNT VS HISTORICAL DEFAULT
-- ============================================================

SELECT
    delay_month_count,

    COUNT(*) AS total_customers,

    SUM(default_next_month)
        AS default_customers,

    ROUND(
        AVG(default_next_month) * 100,
        2
    ) AS historical_default_rate_pct,

    ROUND(
        AVG(latest_utilization_ratio) * 100,
        2
    ) AS average_latest_utilization_pct,

    ROUND(
        AVG(credit_limit),
        2
    ) AS average_credit_limit

FROM credit_profiles

GROUP BY delay_month_count

ORDER BY delay_month_count;



-- ============================================================
-- D2 - MAXIMUM DELAY STATUS VS HISTORICAL DEFAULT
-- ============================================================

SELECT
    max_delay_status,

    COUNT(*) AS total_customers,

    SUM(default_next_month)
        AS default_customers,

    ROUND(
        AVG(default_next_month) * 100,
        2
    ) AS historical_default_rate_pct,

    ROUND(
        AVG(latest_utilization_ratio) * 100,
        2
    ) AS average_latest_utilization_pct

FROM credit_profiles

GROUP BY max_delay_status

ORDER BY max_delay_status;





-- ============================================================
-- D3 - UTILIZATION BAND ANALYSIS
-- These are analytical bands, NOT final risk classifications.
-- ============================================================

SELECT
    CASE
        WHEN latest_utilization_ratio < 0 THEN 'Negative Balance'
        WHEN latest_utilization_ratio < 0.30 THEN 'Below 30%'
        WHEN latest_utilization_ratio < 0.50 THEN '30%-49%'
        WHEN latest_utilization_ratio < 0.70 THEN '50%-69%'
        WHEN latest_utilization_ratio <= 1.00 THEN '70%-100%'
        ELSE 'Above 100%'
    END AS utilization_band,

    COUNT(*) AS total_customers,

    SUM(default_next_month)
        AS default_customers,

    ROUND(
        AVG(default_next_month) * 100,
        2
    ) AS historical_default_rate_pct,

    ROUND(
        AVG(credit_limit),
        2
    ) AS average_credit_limit

FROM credit_profiles

GROUP BY
    CASE
        WHEN latest_utilization_ratio < 0 THEN 'Negative Balance'
        WHEN latest_utilization_ratio < 0.30 THEN 'Below 30%'
        WHEN latest_utilization_ratio < 0.50 THEN '30%-49%'
        WHEN latest_utilization_ratio < 0.70 THEN '50%-69%'
        WHEN latest_utilization_ratio <= 1.00 THEN '70%-100%'
        ELSE 'Above 100%'
    END

ORDER BY
    MIN(latest_utilization_ratio);





-- ============================================================
-- D4 - PAYMENT TO BILL RATIO
-- ============================================================

SELECT
    CASE
        WHEN total_bill_amount_6m <= 0
            THEN 'Non-positive Total Bill'

        WHEN (
            total_payment_amount_6m
            / total_bill_amount_6m
        ) < 0.20
            THEN 'Below 20%'

        WHEN (
            total_payment_amount_6m
            / total_bill_amount_6m
        ) < 0.50
            THEN '20%-49%'

        WHEN (
            total_payment_amount_6m
            / total_bill_amount_6m
        ) < 1.00
            THEN '50%-99%'

        ELSE '100% or More'

    END AS payment_to_bill_band,

    COUNT(*) AS total_customers,

    SUM(default_next_month)
        AS default_customers,

    ROUND(
        AVG(default_next_month) * 100,
        2
    ) AS historical_default_rate_pct

FROM credit_profiles

GROUP BY
    CASE
        WHEN total_bill_amount_6m <= 0
            THEN 'Non-positive Total Bill'

        WHEN (
            total_payment_amount_6m
            / total_bill_amount_6m
        ) < 0.20
            THEN 'Below 20%'

        WHEN (
            total_payment_amount_6m
            / total_bill_amount_6m
        ) < 0.50
            THEN '20%-49%'

        WHEN (
            total_payment_amount_6m
            / total_bill_amount_6m
        ) < 1.00
            THEN '50%-99%'

        ELSE '100% or More'
    END

ORDER BY
    historical_default_rate_pct DESC;




-- ============================================================
-- PHASE 4E - MONTHLY CREDIT ACTIVITY TRENDS
-- ============================================================

SELECT
    activity_month,

    COUNT(DISTINCT customer_id)
        AS total_customers,

    SUM(bill_amount)
        AS total_bill_amount,

    ROUND(
        AVG(bill_amount),
        2
    ) AS average_bill_amount,

    SUM(payment_amount)
        AS total_payment_amount,

    ROUND(
        AVG(payment_amount),
        2
    ) AS average_payment_amount,

    SUM(
        CASE
            WHEN repayment_status > 0 THEN 1
            ELSE 0
        END
    ) AS customers_with_positive_delay,

    ROUND(
        100.0 *
        SUM(
            CASE
                WHEN repayment_status > 0 THEN 1
                ELSE 0
            END
        ) / COUNT(*),
        2
    ) AS positive_delay_rate_pct

FROM monthly_credit_activity

GROUP BY activity_month

ORDER BY activity_month;


-- ============================================================
-- MONTHLY FINANCIAL RECONCILIATION
-- ============================================================

SELECT
    COUNT(*) AS monthly_activity_rows,

    COUNT(DISTINCT customer_id)
        AS unique_customers,

    SUM(bill_amount)
        AS monthly_table_total_bill,

    SUM(payment_amount)
        AS monthly_table_total_payment

FROM monthly_credit_activity;



-- ============================================================
-- PHASE 4F - FINAL ANALYTICS VALIDATION
-- ============================================================
-- ============================================================
-- PHASE 4F - FINAL ANALYTICS VALIDATION
-- ============================================================

SELECT
    (SELECT COUNT(*)
     FROM customers) AS customer_count,

    (SELECT COUNT(*)
     FROM credit_profiles) AS credit_profile_count,

    (SELECT COUNT(*)
     FROM monthly_credit_activity) AS monthly_activity_count,

    (SELECT COUNT(DISTINCT customer_id)
     FROM monthly_credit_activity) AS monthly_unique_customers,

    (SELECT SUM(default_next_month)
     FROM credit_profiles) AS default_customers,

    (SELECT SUM(has_payment_delay)
     FROM credit_profiles) AS delayed_customers,

    (SELECT SUM(
        CASE
            WHEN delay_month_count >= 2 THEN 1
            ELSE 0
        END
     )
     FROM credit_profiles) AS repeated_delay_customers,

    (SELECT SUM(
        CASE
            WHEN latest_utilization_ratio > 1 THEN 1
            ELSE 0
        END
     )
     FROM credit_profiles) AS over_limit_customers,

    (SELECT SUM(total_bill_amount_6m)
     FROM credit_profiles) AS profile_bill_total,

    (SELECT SUM(bill_amount)
     FROM monthly_credit_activity) AS monthly_bill_total,

    (SELECT SUM(total_payment_amount_6m)
     FROM credit_profiles) AS profile_payment_total,

    (SELECT SUM(payment_amount)
     FROM monthly_credit_activity) AS monthly_payment_total;






-- ============================================================
-- PHASE 5E - STORED RISK ASSESSMENT VALIDATION
-- ============================================================

SELECT
    r.risk_band,

    COUNT(*) AS total_customers,

    SUM(cp.default_next_month)
        AS historical_defaults,

    ROUND(
        AVG(cp.default_next_month) * 100,
        2
    ) AS historical_default_rate_pct,

    ROUND(
        AVG(r.risk_score),
        2
    ) AS average_risk_score

FROM customer_risk_assessment r

INNER JOIN credit_profiles cp
    ON r.customer_id = cp.customer_id

GROUP BY r.risk_band

ORDER BY FIELD(
    r.risk_band,
    'LOW',
    'MEDIUM',
    'HIGH'
);