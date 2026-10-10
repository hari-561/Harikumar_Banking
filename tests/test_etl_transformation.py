
import sys
from pathlib import Path
from decimal import Decimal

import pandas as pd
import pytest
from pandas.testing import assert_frame_equal

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "etl"))

from transform import (
    COLUMN_MAPPING,
    BILL_COLUMNS,
    PAYMENT_COLUMNS,
    REPAYMENT_COLUMNS,
    calculate_utilization_ratio,
    transform_data,
)


@pytest.fixture
def raw_data():
    """Two valid banking records with predictable calculations."""

    rows = []

    for customer_id in (1, 2):
        row = {
            "ID": customer_id,
            "LIMIT_BAL": 100000,
            "SEX": 1 if customer_id == 1 else 2,
            "EDUCATION": 1 if customer_id == 1 else 2,
            "MARRIAGE": 1 if customer_id == 1 else 2,
            "AGE": 30,
            "default payment next month": customer_id - 1,
        }

        for column in (
            "PAY_0", "PAY_2", "PAY_3",
            "PAY_4", "PAY_5", "PAY_6"
        ):
            row[column] = 0

        for month in range(1, 7):
            row[f"BILL_AMT{month}"] = 10000
            row[f"PAY_AMT{month}"] = 2000

        rows.append(row)

    return pd.DataFrame(rows)


def test_column_mapping_is_complete(raw_data):
    assert len(COLUMN_MAPPING) == 25
    assert set(raw_data.columns) == set(COLUMN_MAPPING)

    result = transform_data(raw_data)

    for target_column in COLUMN_MAPPING.values():
        assert target_column in result.columns

    for source_column in COLUMN_MAPPING:
        if source_column not in COLUMN_MAPPING.values():
            assert source_column not in result.columns


def test_transformation_row_and_column_counts(raw_data):
    result = transform_data(raw_data)

    assert len(result) == len(raw_data)
    assert len(result.columns) == 36
    assert result["customer_id"].tolist() == [1, 2]


def test_demographic_mapping(raw_data):
    result = transform_data(raw_data)

    assert result["gender"].tolist() == ["Male", "Female"]

    assert result["education"].tolist() == [
        "Graduate School",
        "University",
    ]

    assert result["marital_status"].tolist() == [
        "Married",
        "Single",
    ]


@pytest.mark.parametrize(
    "education_code, expected_label",
    [
        (0, "Others"),
        (1, "Graduate School"),
        (2, "University"),
        (3, "High School"),
        (4, "Others"),
        (5, "Others"),
        (6, "Others"),
    ],
)
def test_education_mapping(
    raw_data, education_code, expected_label
):
    df = raw_data.iloc[[0]].copy()
    df["EDUCATION"] = education_code

    result = transform_data(df)

    assert result.iloc[0]["education"] == expected_label
    assert result.iloc[0]["education_code"] == education_code


@pytest.mark.parametrize(
    "marriage_code, expected_label",
    [
        (0, "Others"),
        (1, "Married"),
        (2, "Single"),
        (3, "Others"),
    ],
)
def test_marital_status_mapping(
    raw_data, marriage_code, expected_label
):
    df = raw_data.iloc[[0]].copy()
    df["MARRIAGE"] = marriage_code

    result = transform_data(df)

    assert result.iloc[0]["marital_status"] == expected_label
    assert result.iloc[0]["marital_status_code"] == marriage_code


@pytest.mark.parametrize(
    "statuses, expected_count, expected_max",
    [
        ([0, 0, 0, 0, 0, 0], 0, 0),
        ([-2, -1, 0, -2, -1, 0], 0, 0),
        ([1, 0, 0, 0, 0, 0], 1, 1),
        ([1, 2, 0, -1, 3, 0], 3, 3),
        ([8, 7, 6, 5, 4, 3], 6, 8),
    ],
)
def test_repayment_delay_metrics(
    raw_data, statuses, expected_count, expected_max
):
    df = raw_data.iloc[[0]].copy()

    source_columns = [
        "PAY_0", "PAY_2", "PAY_3",
        "PAY_4", "PAY_5", "PAY_6"
    ]

    for column, value in zip(source_columns, statuses):
        df.loc[df.index[0], column] = value

    result = transform_data(df)
    row = result.iloc[0]

    assert row["delay_month_count"] == expected_count
    assert row["max_delay_status"] == expected_max
    assert bool(row["has_payment_delay"]) == (expected_count > 0)


def test_bill_metrics(raw_data):
    df = raw_data.iloc[[0]].copy()

    values = [1000, 2000, 3000, 4000, 5000, 6000]

    for month, amount in enumerate(values, start=1):
        df.loc[df.index[0], f"BILL_AMT{month}"] = amount

    result = transform_data(df)
    row = result.iloc[0]

    assert row["total_bill_amount_6m"] == 21000
    assert row["average_bill_amount_6m"] == 3500


def test_payment_metrics(raw_data):
    df = raw_data.iloc[[0]].copy()

    values = [100, 200, 300, 400, 500, 600]

    for month, amount in enumerate(values, start=1):
        df.loc[df.index[0], f"PAY_AMT{month}"] = amount

    result = transform_data(df)
    row = result.iloc[0]

    assert row["total_payment_amount_6m"] == 2100
    assert row["average_payment_amount_6m"] == 350


def test_negative_bill_balance_is_preserved(raw_data):
    df = raw_data.iloc[[0]].copy()
    df.loc[df.index[0], "BILL_AMT1"] = -500

    result = transform_data(df)
    row = result.iloc[0]

    assert row["bill_amount_sep"] == -500
    assert row["total_bill_amount_6m"] == 49500
    assert row["latest_utilization_ratio"] == -0.005


def test_utilization_above_one_is_not_capped(raw_data):
    df = raw_data.iloc[[0]].copy()

    df.loc[df.index[0], "LIMIT_BAL"] = 10000
    df.loc[df.index[0], "BILL_AMT1"] = 15000

    result = transform_data(df)

    assert result.iloc[0]["latest_utilization_ratio"] == 1.5


@pytest.mark.parametrize(
    "bill, limit, expected",
    [
        (1, 3, 0.333333),
        (2, 3, 0.666667),
        (1, 2000000, 0.000001),
        (0, 100000, 0.0),
        (100000, 100000, 1.0),
        (150000, 100000, 1.5),
    ],
)
def test_utilization_rounding(bill, limit, expected):
    row = pd.Series({
        "bill_amount_sep": bill,
        "credit_limit": limit,
    })

    result = calculate_utilization_ratio(row)

    assert result == expected


def test_utilization_half_up_rounding():
    row = pd.Series({
        "bill_amount_sep": Decimal("0.0000005"),
        "credit_limit": 1,
    })

    assert calculate_utilization_ratio(row) == 0.000001


def test_source_financial_values_preserved(raw_data):
    result = transform_data(raw_data)

    for source_column, curated_column in COLUMN_MAPPING.items():
        assert result[curated_column].tolist() == (
            raw_data[source_column].tolist()
        )


def test_input_dataframe_not_modified(raw_data):
    original = raw_data.copy(deep=True)

    transform_data(raw_data)

    assert_frame_equal(raw_data, original)


def test_default_target_preserved(raw_data):
    result = transform_data(raw_data)

    assert result["default_next_month"].tolist() == [0, 1]


def test_important_column_order(raw_data):
    result = transform_data(raw_data)

    assert result.columns[:9].tolist() == [
        "customer_id",
        "credit_limit",
        "gender_code",
        "gender",
        "education_code",
        "education",
        "marital_status_code",
        "marital_status",
        "age",
    ]


def test_six_month_columns_present(raw_data):
    result = transform_data(raw_data)

    for column in (
        REPAYMENT_COLUMNS + BILL_COLUMNS + PAYMENT_COLUMNS
    ):
        assert column in result.columns
