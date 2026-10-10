-- ============================================================
-- BANKING LOAN RISK ANALYSIS
-- DATABASE SCHEMA
-- ============================================================


-- ============================================================
-- 1. CREATE DATABASE
-- ============================================================

CREATE DATABASE IF NOT EXISTS banking_loan_db;

USE banking_loan_db;


-- ============================================================
-- 2. GENDER LOOKUP
-- ============================================================

CREATE TABLE IF NOT EXISTS dim_gender (
    gender_code TINYINT PRIMARY KEY,
    gender_name VARCHAR(20) NOT NULL UNIQUE
);


-- ============================================================
-- 3. EDUCATION LOOKUP
-- ============================================================

CREATE TABLE IF NOT EXISTS dim_education (
    education_code TINYINT PRIMARY KEY,
    education_name VARCHAR(30) NOT NULL
);


-- ============================================================
-- 4. MARITAL STATUS LOOKUP
-- ============================================================

CREATE TABLE IF NOT EXISTS dim_marital_status (
    marital_status_code TINYINT PRIMARY KEY,
    marital_status_name VARCHAR(20) NOT NULL
);


-- ============================================================
-- 5. CUSTOMERS
-- ============================================================

CREATE TABLE IF NOT EXISTS customers (
    customer_id INT PRIMARY KEY,

    gender_code TINYINT NOT NULL,
    education_code TINYINT NOT NULL,
    marital_status_code TINYINT NOT NULL,

    age TINYINT UNSIGNED NOT NULL,

    CONSTRAINT fk_customer_gender
        FOREIGN KEY (gender_code)
        REFERENCES dim_gender(gender_code),

    CONSTRAINT fk_customer_education
        FOREIGN KEY (education_code)
        REFERENCES dim_education(education_code),

    CONSTRAINT fk_customer_marital_status
        FOREIGN KEY (marital_status_code)
        REFERENCES dim_marital_status(marital_status_code)
);


-- ============================================================
-- 6. CREDIT PROFILE
-- ============================================================

CREATE TABLE IF NOT EXISTS credit_profiles (
    customer_id INT PRIMARY KEY,

    credit_limit DECIMAL(12,2) NOT NULL,

    delay_month_count TINYINT UNSIGNED NOT NULL,
    max_delay_status TINYINT UNSIGNED NOT NULL,
    has_payment_delay BOOLEAN NOT NULL,

    total_bill_amount_6m DECIMAL(14,2) NOT NULL,
    average_bill_amount_6m DECIMAL(14,2) NOT NULL,

    total_payment_amount_6m DECIMAL(14,2) NOT NULL,
    average_payment_amount_6m DECIMAL(14,2) NOT NULL,

    latest_utilization_ratio DECIMAL(12,6) NOT NULL,

    default_next_month TINYINT NOT NULL,

    CONSTRAINT fk_credit_customer
        FOREIGN KEY (customer_id)
        REFERENCES customers(customer_id),

    CONSTRAINT chk_credit_limit
        CHECK (credit_limit > 0),

    CONSTRAINT chk_delay_month_count
        CHECK (delay_month_count BETWEEN 0 AND 6),

    CONSTRAINT chk_default_next_month
        CHECK (default_next_month IN (0, 1))
);


-- ============================================================
-- 7. MONTHLY CREDIT ACTIVITY
-- ============================================================

CREATE TABLE IF NOT EXISTS monthly_credit_activity (
    activity_id BIGINT AUTO_INCREMENT PRIMARY KEY,

    customer_id INT NOT NULL,

    activity_month DATE NOT NULL,

    repayment_status TINYINT NOT NULL,

    bill_amount DECIMAL(14,2) NOT NULL,

    payment_amount DECIMAL(14,2) NOT NULL,

    CONSTRAINT fk_activity_customer
        FOREIGN KEY (customer_id)
        REFERENCES customers(customer_id),

    CONSTRAINT uq_customer_month
        UNIQUE (customer_id, activity_month),

    CONSTRAINT chk_repayment_status
        CHECK (repayment_status BETWEEN -2 AND 8),

    CONSTRAINT chk_payment_amount
        CHECK (payment_amount >= 0)
);


-- ============================================================
-- 8. INDEXES
-- ============================================================

CREATE INDEX idx_customer_gender
ON customers(gender_code);

CREATE INDEX idx_customer_education
ON customers(education_code);

CREATE INDEX idx_customer_marital_status
ON customers(marital_status_code);

CREATE INDEX idx_customer_age
ON customers(age);


CREATE INDEX idx_credit_default
ON credit_profiles(default_next_month);

CREATE INDEX idx_credit_delay
ON credit_profiles(delay_month_count);

CREATE INDEX idx_credit_utilization
ON credit_profiles(latest_utilization_ratio);


CREATE INDEX idx_activity_month
ON monthly_credit_activity(activity_month);

CREATE INDEX idx_activity_repayment
ON monthly_credit_activity(repayment_status);


-- ============================================================
-- 9. LOOKUP DATA
-- ============================================================

INSERT IGNORE INTO dim_gender
(gender_code, gender_name)
VALUES
    (1, 'Male'),
    (2, 'Female');


INSERT IGNORE INTO dim_education
(education_code, education_name)
VALUES
    (0, 'Others'),
    (1, 'Graduate School'),
    (2, 'University'),
    (3, 'High School'),
    (4, 'Others'),
    (5, 'Others'),
    (6, 'Others');


INSERT IGNORE INTO dim_marital_status
(marital_status_code, marital_status_name)
VALUES
    (0, 'Others'),
    (1, 'Married'),
    (2, 'Single'),
    (3, 'Others');



-- ============================================================
-- ETL BATCH AUDIT
-- ============================================================

CREATE TABLE IF NOT EXISTS etl_batch_audit (
    batch_id BIGINT AUTO_INCREMENT PRIMARY KEY,

    source_file VARCHAR(255) NOT NULL,

    start_time DATETIME NOT NULL,
    end_time DATETIME NULL,

    source_record_count INT NOT NULL DEFAULT 0,

    new_record_count INT NOT NULL DEFAULT 0,
    updated_record_count INT NOT NULL DEFAULT 0,
    unchanged_record_count INT NOT NULL DEFAULT 0,

    loaded_record_count INT NOT NULL DEFAULT 0,
    failed_record_count INT NOT NULL DEFAULT 0,

    status VARCHAR(20) NOT NULL,

    error_message TEXT NULL
);





-- ============================================================
-- CUSTOMER RISK ASSESSMENT
-- ============================================================

CREATE TABLE IF NOT EXISTS customer_risk_assessment (

    customer_id INT PRIMARY KEY,

    payment_to_bill_ratio DECIMAL(12,6) NULL,

    delay_frequency_score TINYINT NOT NULL,
    delay_severity_score TINYINT NOT NULL,
    utilization_score TINYINT NOT NULL,
    payment_behavior_score TINYINT NOT NULL,

    risk_score TINYINT NOT NULL,

    risk_band ENUM(
        'LOW',
        'MEDIUM',
        'HIGH'
    ) NOT NULL,

    rule_version VARCHAR(20) NOT NULL DEFAULT '1.0',

    assessed_at TIMESTAMP
        NOT NULL
        DEFAULT CURRENT_TIMESTAMP
        ON UPDATE CURRENT_TIMESTAMP,

    CONSTRAINT fk_risk_customer
        FOREIGN KEY (customer_id)
        REFERENCES customers(customer_id),

    CONSTRAINT chk_delay_frequency_score
        CHECK (delay_frequency_score BETWEEN 0 AND 3),

    CONSTRAINT chk_delay_severity_score
        CHECK (delay_severity_score BETWEEN 0 AND 3),

    CONSTRAINT chk_utilization_score
        CHECK (utilization_score BETWEEN 0 AND 3),

    CONSTRAINT chk_payment_behavior_score
        CHECK (payment_behavior_score BETWEEN 0 AND 2),

    CONSTRAINT chk_risk_score
        CHECK (risk_score BETWEEN 0 AND 11)
);


CREATE INDEX idx_risk_band
ON customer_risk_assessment(risk_band);


CREATE INDEX idx_risk_score
ON customer_risk_assessment(risk_score);




CREATE TABLE IF NOT EXISTS app_users (
    user_id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(100) NOT NULL UNIQUE,
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    role ENUM('ADMIN', 'ANALYST', 'VIEWER') NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL
        DEFAULT CURRENT_TIMESTAMP
        ON UPDATE CURRENT_TIMESTAMP
);