
import sys
from pathlib import Path
from unittest.mock import patch

import pandas as pd
import pytest
from pandas.testing import assert_frame_equal

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "etl"))

import prepare_tables as prep


@pytest.fixture
def curated_data():
    """Create two curated customer records with distinct monthly data."""

    records = []

    for customer_id in (1, 2):
        record = {
            "customer_id": customer_id,
            "credit_limit": 100000 * customer_id,
            "gender_code": customer_id,
            "education_code": 2,
            "marital_status_code": 1,
            "age": 25 + customer_id,
            "delay_month_count": 1,
            "max_delay_status": 2,
            "has_payment_delay": True,
            "total_bill_amount_6m": 21000 * customer_id,
            "average_bill_amount_6m": 3500 * customer_id,
            "total_payment_amount_6m": 2100 * customer_id,
            "average_payment_amount_6m": 350 * customer_id,
            "latest_utilization_ratio": 0.01,
            "default_next_month": customer_id - 1,
        }

        for month_number, month_name in enumerate(
            ["sep", "aug", "jul", "jun", "may", "apr"],
            start=1,
        ):
            record[f"repayment_status_{month_name}"] = (
                month_number - 1
            )
            record[f"bill_amount_{month_name}"] = (
                1000 * month_number * customer_id
            )
            record[f"payment_amount_{month_name}"] = (
                100 * month_number * customer_id
            )

        records.append(record)

    return pd.DataFrame(records)


@pytest.fixture
def risk_data():
    return pd.DataFrame([
        {
            "customer_id": 1,
            "payment_to_bill_ratio": 0.4,
            "delay_frequency_score": 20,
            "delay_severity_score": 30,
            "utilization_score": 10,
            "payment_behavior_score": 15,
            "risk_score": 75,
            "risk_band": "HIGH",
            "extra_column": "ignored",
        },
        {
            "customer_id": 2,
            "payment_to_bill_ratio": 0.8,
            "delay_frequency_score": 5,
            "delay_severity_score": 10,
            "utilization_score": 5,
            "payment_behavior_score": 5,
            "risk_score": 25,
            "risk_band": "LOW",
            "extra_column": "ignored",
        },
    ])


def test_prepare_customers_columns(curated_data):
    result = prep.prepare_customers(curated_data)

    assert result.columns.tolist() == [
        "customer_id",
        "gender_code",
        "education_code",
        "marital_status_code",
        "age",
    ]
    assert len(result) == 2
    assert result["customer_id"].tolist() == [1, 2]


def test_prepare_customers_values(curated_data):
    result = prep.prepare_customers(curated_data)

    assert result["gender_code"].tolist() == [1, 2]
    assert result["age"].tolist() == [26, 27]


def test_prepare_credit_profiles_columns(curated_data):
    result = prep.prepare_credit_profiles(curated_data)

    assert result.columns.tolist() == [
        "customer_id",
        "credit_limit",
        "delay_month_count",
        "max_delay_status",
        "has_payment_delay",
        "total_bill_amount_6m",
        "average_bill_amount_6m",
        "total_payment_amount_6m",
        "average_payment_amount_6m",
        "latest_utilization_ratio",
        "default_next_month",
    ]


def test_prepare_credit_profiles_values(curated_data):
    result = prep.prepare_credit_profiles(curated_data)

    assert len(result) == 2
    assert result["credit_limit"].tolist() == [100000, 200000]
    assert result["default_next_month"].tolist() == [0, 1]
    assert result["total_bill_amount_6m"].tolist() == [
        21000, 42000
    ]


def test_month_mapping_has_six_unique_months():
    months = [item["month"] for item in prep.MONTH_MAPPING]

    assert months == [
        "2005-09-01",
        "2005-08-01",
        "2005-07-01",
        "2005-06-01",
        "2005-05-01",
        "2005-04-01",
    ]

    assert len(months) == len(set(months)) == 6


def test_monthly_activity_row_count(curated_data):
    result = prep.prepare_monthly_activity(curated_data)

    assert len(result) == 12
    assert result["customer_id"].nunique() == 2


def test_monthly_activity_columns(curated_data):
    result = prep.prepare_monthly_activity(curated_data)

    assert result.columns.tolist() == [
        "customer_id",
        "activity_month",
        "repayment_status",
        "bill_amount",
        "payment_amount",
    ]


def test_monthly_activity_has_six_rows_per_customer(curated_data):
    result = prep.prepare_monthly_activity(curated_data)

    counts = result.groupby("customer_id").size()

    assert counts.to_dict() == {1: 6, 2: 6}


def test_monthly_activity_has_no_duplicate_customer_month(
    curated_data,
):
    result = prep.prepare_monthly_activity(curated_data)

    assert not result.duplicated(
        subset=["customer_id", "activity_month"]
    ).any()


def test_monthly_activity_sorted_by_customer_and_month(
    curated_data,
):
    result = prep.prepare_monthly_activity(curated_data)

    expected = result.sort_values(
        ["customer_id", "activity_month"]
    ).reset_index(drop=True)

    assert_frame_equal(result, expected)


def test_monthly_activity_dates(curated_data):
    result = prep.prepare_monthly_activity(curated_data)

    dates = (
        result.loc[result["customer_id"] == 1, "activity_month"]
        .dt.strftime("%Y-%m-%d")
        .tolist()
    )

    assert dates == [
        "2005-04-01",
        "2005-05-01",
        "2005-06-01",
        "2005-07-01",
        "2005-08-01",
        "2005-09-01",
    ]


def test_monthly_activity_values(curated_data):
    result = prep.prepare_monthly_activity(curated_data)

    september = result.loc[
        (result["customer_id"] == 2)
        & (result["activity_month"] == pd.Timestamp("2005-09-01"))
    ].iloc[0]

    assert september["repayment_status"] == 0
    assert september["bill_amount"] == 2000
    assert september["payment_amount"] == 200

    april = result.loc[
        (result["customer_id"] == 1)
        & (result["activity_month"] == pd.Timestamp("2005-04-01"))
    ].iloc[0]

    assert april["repayment_status"] == 5
    assert april["bill_amount"] == 6000
    assert april["payment_amount"] == 600


def test_database_tables_reconciliation(curated_data):
    customers, profiles, monthly = (
        prep.prepare_database_tables(curated_data)
    )

    assert len(customers) == 2
    assert len(profiles) == 2
    assert len(monthly) == 12

    assert set(customers["customer_id"]) == {1, 2}
    assert set(profiles["customer_id"]) == {1, 2}
    assert set(monthly["customer_id"]) == {1, 2}


def test_database_tables_reconciliation_success_logged(
    curated_data,
):
    with patch.object(prep.logger, "info") as mock_info:
        prep.prepare_database_tables(curated_data)

    assert any(
        "reconciliation passed" in str(call).lower()
        for call in mock_info.call_args_list
    )


def test_database_tables_reconciliation_failure_logged(
    curated_data,
):
    incomplete_monthly = pd.DataFrame({
        "customer_id": [1],
        "activity_month": [pd.Timestamp("2005-09-01")],
    })

    with patch.object(
        prep,
        "prepare_monthly_activity",
        return_value=incomplete_monthly,
    ):
        with patch.object(prep.logger, "error") as mock_error:
            customers, profiles, monthly = (
                prep.prepare_database_tables(curated_data)
            )

    assert len(customers) == 2
    assert len(profiles) == 2
    assert len(monthly) == 1

    assert any(
        "reconciliation failed" in str(call).lower()
        for call in mock_error.call_args_list
    )


def test_risk_assessments_columns(risk_data):
    result = prep.prepare_risk_assessments(risk_data)

    assert result.columns.tolist() == [
        "customer_id",
        "payment_to_bill_ratio",
        "delay_frequency_score",
        "delay_severity_score",
        "utilization_score",
        "payment_behavior_score",
        "risk_score",
        "risk_band",
        "rule_version",
    ]


def test_risk_assessments_rule_version(risk_data):
    result = prep.prepare_risk_assessments(risk_data)

    assert len(result) == 2
    assert result["rule_version"].tolist() == ["1.0", "1.0"]
    assert result["risk_band"].tolist() == ["HIGH", "LOW"]


@pytest.mark.parametrize(
    "missing_column",
    [
        "customer_id",
        "payment_to_bill_ratio",
        "delay_frequency_score",
        "delay_severity_score",
        "utilization_score",
        "payment_behavior_score",
        "risk_score",
        "risk_band",
    ],
)
def test_risk_assessments_missing_column(
    risk_data, missing_column
):
    df = risk_data.drop(columns=[missing_column])

    with pytest.raises(
        ValueError, match="Missing risk assessment columns"
    ):
        prep.prepare_risk_assessments(df)


def test_risk_assessments_does_not_modify_input(risk_data):
    original = risk_data.copy(deep=True)

    prep.prepare_risk_assessments(risk_data)

    assert_frame_equal(risk_data, original)


def test_prepare_functions_do_not_modify_input(curated_data):
    original = curated_data.copy(deep=True)

    prep.prepare_database_tables(curated_data)

    assert_frame_equal(curated_data, original)
