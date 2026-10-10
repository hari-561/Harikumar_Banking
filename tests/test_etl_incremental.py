
import sys
from decimal import Decimal
from pathlib import Path
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest
from pandas.testing import assert_frame_equal

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "etl"))

import incremental as inc


@pytest.fixture
def existing_data():
    """Three customers in the existing warehouse."""

    rows = []

    for customer_id in (1, 2, 3):
        rows.append({
            "customer_id": customer_id,
            "credit_limit": 100000 * customer_id,
            "gender_code": 1,
            "education_code": 2,
            "marital_status_code": 1,
            "age": 30,
            "delay_month_count": 1,
            "max_delay_status": 2,
            "has_payment_delay": True,
            "total_bill_amount_6m": 60000,
            "average_bill_amount_6m": 10000,
            "total_payment_amount_6m": 12000,
            "average_payment_amount_6m": 2000,
            "latest_utilization_ratio": 0.123456,
            "default_next_month": 0,
        })

    return pd.DataFrame(rows)


def test_comparison_schema(existing_data):
    result = inc.normalize_for_comparison(existing_data)

    assert result.columns.tolist() == inc.COMPARE_COLUMNS
    assert len(result.columns) == 15


def test_integer_normalization(existing_data):
    df = existing_data.copy()
    df["customer_id"] = df["customer_id"].astype(str)
    df["age"] = df["age"].astype(str)

    result = inc.normalize_for_comparison(df)

    assert result["customer_id"].dtype == "int64"
    assert result["age"].dtype == "int64"
    assert result["customer_id"].tolist() == [1, 2, 3]


def test_boolean_normalization(existing_data):
    df = existing_data.copy()
    df["has_payment_delay"] = [1, 0, 1]

    result = inc.normalize_for_comparison(df)

    assert result["has_payment_delay"].tolist() == [
        True, False, True
    ]


@pytest.mark.parametrize(
    "value, expected",
    [
        (0.1234561, 0.123456),
        (0.1234564, 0.123456),
        (0.1234568, 0.123457),
    ],
)
def test_decimal_precision(existing_data, value, expected):
    df = existing_data.copy()
    df.loc[0, "latest_utilization_ratio"] = value

    result = inc.normalize_for_comparison(df)

    assert result.loc[0, "latest_utilization_ratio"] == expected


def test_mysql_decimal_normalization(existing_data):
    df = existing_data.copy()

    df["credit_limit"] = df["credit_limit"].map(
        lambda value: Decimal(str(value))
    )
    df["latest_utilization_ratio"] = df[
        "latest_utilization_ratio"
    ].map(lambda value: Decimal(str(value)))

    result = inc.normalize_for_comparison(df)

    assert result["credit_limit"].tolist() == [
        100000.0, 200000.0, 300000.0
    ]
    assert result["latest_utilization_ratio"].tolist() == [
        0.123456, 0.123456, 0.123456
    ]


def test_normalization_does_not_modify_input(existing_data):
    original = existing_data.copy(deep=True)

    inc.normalize_for_comparison(existing_data)

    assert_frame_equal(existing_data, original)


def test_identical_records_unchanged(existing_data):
    new, changed, unchanged = inc.detect_changes(
        existing_data.copy(),
        existing_data.copy(),
    )

    assert len(new) == 0
    assert len(changed) == 0
    assert unchanged["customer_id"].tolist() == [1, 2, 3]


def test_new_customer_detected(existing_data):
    incoming = existing_data.copy()

    new_customer = existing_data.iloc[[0]].copy()
    new_customer["customer_id"] = 4

    incoming = pd.concat(
        [incoming, new_customer],
        ignore_index=True,
    )

    new, changed, unchanged = inc.detect_changes(
        incoming, existing_data
    )

    assert new["customer_id"].tolist() == [4]
    assert changed.empty
    assert len(unchanged) == 3


def test_changed_credit_limit_detected(existing_data):
    incoming = existing_data.copy()
    incoming.loc[1, "credit_limit"] = 999999

    new, changed, unchanged = inc.detect_changes(
        incoming, existing_data
    )

    assert new.empty
    assert changed["customer_id"].tolist() == [2]
    assert set(unchanged["customer_id"]) == {1, 3}


def test_changed_demographic_detected(existing_data):
    incoming = existing_data.copy()
    incoming.loc[0, "age"] = 31

    _, changed, _ = inc.detect_changes(
        incoming, existing_data
    )

    assert changed["customer_id"].tolist() == [1]


def test_changed_default_target_detected(existing_data):
    incoming = existing_data.copy()
    incoming.loc[2, "default_next_month"] = 1

    _, changed, _ = inc.detect_changes(
        incoming, existing_data
    )

    assert changed["customer_id"].tolist() == [3]


def test_changed_payment_delay_detected(existing_data):
    incoming = existing_data.copy()
    incoming.loc[0, "has_payment_delay"] = False

    _, changed, _ = inc.detect_changes(
        incoming, existing_data
    )

    assert changed["customer_id"].tolist() == [1]


def test_small_decimal_difference_ignored(existing_data):
    incoming = existing_data.copy()

    incoming.loc[0, "latest_utilization_ratio"] = 0.1234561

    new, changed, unchanged = inc.detect_changes(
        incoming, existing_data
    )

    assert new.empty
    assert changed.empty
    assert len(unchanged) == 3


def test_significant_decimal_difference_detected(existing_data):
    incoming = existing_data.copy()

    incoming.loc[0, "latest_utilization_ratio"] = 0.123457

    _, changed, _ = inc.detect_changes(
        incoming, existing_data
    )

    assert changed["customer_id"].tolist() == [1]


def test_mysql_numeric_representations_match(existing_data):
    incoming = existing_data.copy()
    existing = existing_data.copy()

    existing["credit_limit"] = existing[
        "credit_limit"
    ].map(lambda value: Decimal(str(value)))

    existing["latest_utilization_ratio"] = existing[
        "latest_utilization_ratio"
    ].map(lambda value: Decimal(str(value)))

    _, changed, unchanged = inc.detect_changes(
        incoming, existing
    )

    assert changed.empty
    assert len(unchanged) == 3


def test_mixed_new_changed_unchanged(existing_data):
    incoming = existing_data.copy()

    incoming.loc[1, "credit_limit"] = 999999

    new_customer = existing_data.iloc[[0]].copy()
    new_customer["customer_id"] = 4

    incoming = pd.concat(
        [incoming, new_customer],
        ignore_index=True,
    )

    new, changed, unchanged = inc.detect_changes(
        incoming, existing_data
    )

    assert new["customer_id"].tolist() == [4]
    assert changed["customer_id"].tolist() == [2]
    assert set(unchanged["customer_id"]) == {1, 3}

    assert len(new) + len(changed) + len(unchanged) == len(
        incoming
    )


def test_empty_existing_dataset(existing_data):
    empty_existing = existing_data.iloc[0:0].copy()

    new, changed, unchanged = inc.detect_changes(
        existing_data, empty_existing
    )

    assert len(new) == 3
    assert changed.empty
    assert unchanged.empty


def test_empty_incoming_dataset(existing_data):
    empty_incoming = existing_data.iloc[0:0].copy()

    new, changed, unchanged = inc.detect_changes(
        empty_incoming, existing_data
    )

    assert new.empty
    assert changed.empty
    assert unchanged.empty


def test_detection_preserves_input(existing_data):
    incoming = existing_data.copy()
    original = incoming.copy(deep=True)

    inc.detect_changes(incoming, existing_data)

    assert_frame_equal(incoming, original)


def test_diagnose_no_changes(existing_data, capsys):
    inc.diagnose_changes(
        existing_data,
        existing_data,
        existing_data.iloc[0:0],
    )

    output = capsys.readouterr().out

    assert "No changed records to diagnose" in output


def test_diagnose_changed_field(existing_data, capsys):
    incoming = existing_data.copy()
    incoming.loc[0, "credit_limit"] = 150000

    _, changed, _ = inc.detect_changes(
        incoming, existing_data
    )

    inc.diagnose_changes(incoming, existing_data, changed)

    output = capsys.readouterr().out

    assert "credit_limit: 1" in output
    assert "Customer 1" in output
    assert "incoming=150000" in output


def test_fetch_existing_customers_success(existing_data):
    connection = MagicMock()
    cursor = MagicMock()

    connection.cursor.return_value = cursor
    connection.is_connected.return_value = True

    cursor.fetchall.return_value = existing_data.to_dict(
        orient="records"
    )

    with patch.object(
        inc, "get_connection", return_value=connection
    ):
        result = inc.fetch_existing_customers()

    assert len(result) == 3
    assert result["customer_id"].tolist() == [1, 2, 3]

    connection.cursor.assert_called_once_with(dictionary=True)
    cursor.execute.assert_called_once()

    query = cursor.execute.call_args.args[0]

    assert "FROM customers c" in query
    assert "INNER JOIN credit_profiles cp" in query

    cursor.close.assert_called_once()
    connection.close.assert_called_once()


def test_fetch_existing_customers_empty_result(existing_data):
    connection = MagicMock()
    cursor = MagicMock()

    connection.cursor.return_value = cursor
    connection.is_connected.return_value = True
    cursor.fetchall.return_value = []

    with patch.object(
        inc, "get_connection", return_value=connection
    ):
        result = inc.fetch_existing_customers()

    assert result.empty
    cursor.close.assert_called_once()
    connection.close.assert_called_once()


def test_fetch_existing_customers_query_error():
    connection = MagicMock()
    cursor = MagicMock()

    connection.cursor.return_value = cursor
    connection.is_connected.return_value = True
    cursor.execute.side_effect = RuntimeError("Mock query error")

    with patch.object(
        inc, "get_connection", return_value=connection
    ):
        with pytest.raises(RuntimeError, match="Mock query error"):
            inc.fetch_existing_customers()

    cursor.close.assert_called_once()
    connection.close.assert_called_once()
