"""
Rule-Based Credit Risk Classification
=====================================

Classifies customers into LOW, MEDIUM, or HIGH risk using
transparent behavioural business rules.

IMPORTANT:
- default_next_month is NOT used to calculate risk.
- demographic attributes are NOT used to calculate risk.
- default_next_month is used only for historical validation.

Risk indicators:
1. Delay frequency
2. Maximum delay severity
3. Latest credit utilization
4. Six-month payment-to-bill ratio
"""

import pandas as pd


# ============================================================
# RISK SCORE FUNCTIONS
# ============================================================

def score_delay_frequency(delay_month_count):
    """
    Score based on the number of months with a positive
    repayment delay.
    """

    if delay_month_count >= 3:
        return 3
    elif delay_month_count == 2:
        return 2
    elif delay_month_count == 1:
        return 1

    return 0


def score_delay_severity(max_delay_status):
    """
    Score based on the most severe positive repayment
    delay observed during the six-month period.
    """

    if max_delay_status >= 3:
        return 3
    elif max_delay_status == 2:
        return 2
    elif max_delay_status == 1:
        return 1

    return 0


def score_utilization(latest_utilization_ratio):
    """
    Score based on the latest bill amount relative
    to the customer's credit limit.

    Negative utilization receives zero risk points.
    """

    if pd.isna(latest_utilization_ratio):
        return 0

    if latest_utilization_ratio > 1:
        return 3
    elif latest_utilization_ratio >= 0.70:
        return 2
    elif latest_utilization_ratio >= 0.50:
        return 1

    return 0


def calculate_payment_to_bill_ratio(
    total_payment_amount_6m,
    total_bill_amount_6m
):
    """
    Calculate the six-month payment-to-bill ratio.

    A ratio is not calculated when the total bill amount
    is zero or negative.
    """

    if pd.isna(total_bill_amount_6m):
        return None

    if pd.isna(total_payment_amount_6m):
        return None

    if total_bill_amount_6m <= 0:
        return None

    return total_payment_amount_6m / total_bill_amount_6m


def score_payment_behavior(payment_to_bill_ratio):
    """
    Score payment behaviour.

    Non-positive total bill amounts produce no payment
    behaviour risk points because the ratio is not
    considered meaningful for this rule.
    """

    if payment_to_bill_ratio is None:
        return 0

    if pd.isna(payment_to_bill_ratio):
        return 0

    if payment_to_bill_ratio < 0.20:
        return 2
    elif payment_to_bill_ratio < 0.50:
        return 1

    return 0


def classify_risk(risk_score):
    """
    Convert the total rule-based score into a risk band.

    Proposed thresholds:
        0-2  -> LOW
        3-5  -> MEDIUM
        6-11 -> HIGH

    These thresholds must be validated against the
    historical default outcome before being finalized.
    """

    if risk_score >= 6:
        return "HIGH"
    elif risk_score >= 3:
        return "MEDIUM"

    return "LOW"


# ============================================================
# CUSTOMER RISK CALCULATION
# ============================================================

def calculate_customer_risk(row):
    """
    Calculate all risk components for one customer.
    """

    payment_to_bill_ratio = calculate_payment_to_bill_ratio(
        row["total_payment_amount_6m"],
        row["total_bill_amount_6m"]
    )

    delay_frequency_score = score_delay_frequency(
        row["delay_month_count"]
    )

    delay_severity_score = score_delay_severity(
        row["max_delay_status"]
    )

    utilization_score = score_utilization(
        row["latest_utilization_ratio"]
    )

    payment_behavior_score = score_payment_behavior(
        payment_to_bill_ratio
    )

    risk_score = (
        delay_frequency_score
        + delay_severity_score
        + utilization_score
        + payment_behavior_score
    )

    risk_band = classify_risk(risk_score)

    return pd.Series({
        "payment_to_bill_ratio": payment_to_bill_ratio,
        "delay_frequency_score": delay_frequency_score,
        "delay_severity_score": delay_severity_score,
        "utilization_score": utilization_score,
        "payment_behavior_score": payment_behavior_score,
        "risk_score": risk_score,
        "risk_band": risk_band
    })


# ============================================================
# APPLY RISK RULES
# ============================================================

def apply_risk_rules(df):
    """
    Apply the rule-based risk classification to all customers.
    """

    required_columns = [
        "customer_id",
        "delay_month_count",
        "max_delay_status",
        "latest_utilization_ratio",
        "total_bill_amount_6m",
        "total_payment_amount_6m"
    ]

    missing_columns = [
        column
        for column in required_columns
        if column not in df.columns
    ]

    if missing_columns:
        raise ValueError(
            f"Missing required risk columns: {missing_columns}"
        )

    result = df.copy()

    risk_results = result.apply(
        calculate_customer_risk,
        axis=1
    )

    result = pd.concat(
        [
            result.reset_index(drop=True),
            risk_results.reset_index(drop=True)
        ],
        axis=1
    )

    return result


# ============================================================
# HISTORICAL VALIDATION
# ============================================================

def validate_risk_bands(df):
    """
    Compare rule-based risk bands with historical default
    outcomes.

    default_next_month is used ONLY here for validation,
    never as an input to the risk score.
    """

    if "default_next_month" not in df.columns:
        raise ValueError(
            "default_next_month is required for historical validation."
        )

    validation = (
        df.groupby("risk_band", observed=True)
        .agg(
            total_customers=("customer_id", "count"),
            default_customers=("default_next_month", "sum"),
            average_risk_score=("risk_score", "mean")
        )
        .reset_index()
    )

    validation["historical_default_rate_pct"] = (
        validation["default_customers"]
        / validation["total_customers"]
        * 100
    ).round(2)

    validation["average_risk_score"] = (
        validation["average_risk_score"].round(2)
    )

    band_order = {
        "LOW": 1,
        "MEDIUM": 2,
        "HIGH": 3
    }

    validation["_order"] = (
        validation["risk_band"].map(band_order)
    )

    validation = (
        validation
        .sort_values("_order")
        .drop(columns="_order")
        .reset_index(drop=True)
    )

    return validation




if __name__ == "__main__":

    import sys
    from pathlib import Path

    PROJECT_ROOT = Path(__file__).resolve().parents[1]

    sys.path.append(str(PROJECT_ROOT))

    from etl.extract import extract_data
    from etl.transform import transform_data

    FILE_PATH = (
        PROJECT_ROOT
        / "data"
        / "raw"
        / "default_of_credit_card_clients.xls"
    )

    print("Loading source data...")

    raw_data = extract_data(FILE_PATH)

    print("Transforming data...")

    transformed_data = transform_data(raw_data)

    print("Applying risk rules...")

    risk_data = apply_risk_rules(transformed_data)

    print("\n========== RISK BAND VALIDATION ==========")

    validation = validate_risk_bands(risk_data)

    print(validation.to_string(index=False))

    print("\n========== RISK SCORE DISTRIBUTION ==========")

    print(
        risk_data["risk_score"]
        .value_counts()
        .sort_index()
        .to_string()
    )

    print("\n========== RECONCILIATION ==========")

    print("Input customers :", len(transformed_data))
    print("Risk customers  :", len(risk_data))
    print(
        "Missing bands   :",
        risk_data["risk_band"].isna().sum()
    )

    print(
        "Min risk score  :",
        risk_data["risk_score"].min()
    )

    print(
        "Max risk score  :",
        risk_data["risk_score"].max()
    )