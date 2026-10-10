
import pandas as pd
import pytest

from src.frontend.pages.customer_management import (
    MONTHS,
    default_monthly_activity,
    validate_monthly_activity,
)


@pytest.fixture
def valid_activity():
    return default_monthly_activity()


def test_default_activity_has_six_rows(valid_activity):
    assert len(valid_activity) == 6
    assert list(valid_activity["activity_month"]) == MONTHS


def test_default_activity_has_required_columns(valid_activity):
    assert list(valid_activity.columns) == [
        "activity_month",
        "repayment_status",
        "bill_amount",
        "payment_amount",
    ]


def test_default_activity_has_zero_values(valid_activity):
    assert (valid_activity["repayment_status"] == 0).all()
    assert (valid_activity["bill_amount"] == 0).all()
    assert (valid_activity["payment_amount"] == 0).all()


def test_valid_activity_returns_six_records(valid_activity):
    result = validate_monthly_activity(valid_activity)

    assert len(result) == 6
    assert all(isinstance(row, dict) for row in result)


def test_valid_activity_preserves_month_order(valid_activity):
    result = validate_monthly_activity(valid_activity)

    assert [
        row["activity_month"] for row in result
    ] == MONTHS


@pytest.mark.parametrize(
    "missing_column",
    [
        "activity_month",
        "repayment_status",
        "bill_amount",
        "payment_amount",
    ],
)
def test_missing_required_column(
    valid_activity, missing_column
):
    invalid = valid_activity.drop(columns=[missing_column])

    with pytest.raises(
        ValueError, match="columns are missing"
    ):
        validate_monthly_activity(invalid)


@pytest.mark.parametrize("row_count", [0, 1, 5, 7])
def test_invalid_activity_row_count(
    valid_activity, row_count
):
    invalid = pd.concat(
        [valid_activity] * 2,
        ignore_index=True,
    ).iloc[:row_count]

    with pytest.raises(
        ValueError, match="Exactly six"
    ):
        validate_monthly_activity(invalid)


@pytest.mark.parametrize(
    "column",
    [
        "activity_month",
        "repayment_status",
        "bill_amount",
        "payment_amount",
    ],
)
def test_missing_activity_value(valid_activity, column):
    valid_activity.loc[0, column] = None

    with pytest.raises(
        ValueError, match="empty values"
    ):
        validate_monthly_activity(valid_activity)


def test_incorrect_month_order(valid_activity):
    invalid = valid_activity.iloc[::-1].reset_index(
        drop=True
    )

    with pytest.raises(
        ValueError, match="chronological order"
    ):
        validate_monthly_activity(invalid)


@pytest.mark.parametrize("status", [-3, 10])
def test_repayment_status_out_of_range(
    valid_activity, status
):
    valid_activity.loc[0, "repayment_status"] = status

    with pytest.raises(
        ValueError, match="between -2 and 9"
    ):
        validate_monthly_activity(valid_activity)


def test_fractional_repayment_status(valid_activity):
    # Convert the integer column to float before
    # inserting a fractional repayment status.
    valid_activity["repayment_status"] = (
        valid_activity["repayment_status"].astype(float)
    )

    valid_activity.loc[0, "repayment_status"] = 1.5

    with pytest.raises(
        ValueError, match="must be an integer"
    ):
        validate_monthly_activity(valid_activity)

def test_negative_payment_rejected(valid_activity):
    valid_activity.loc[0, "payment_amount"] = -100

    with pytest.raises(
        ValueError, match="cannot be negative"
    ):
        validate_monthly_activity(valid_activity)


def test_negative_bill_amount_allowed(valid_activity):
    valid_activity.loc[0, "bill_amount"] = -500

    result = validate_monthly_activity(valid_activity)

    assert result[0]["bill_amount"] == -500.0


@pytest.mark.parametrize("status", [-2, -1, 0, 1, 9])
def test_valid_repayment_status_boundaries(
    valid_activity, status
):
    valid_activity.loc[0, "repayment_status"] = status

    result = validate_monthly_activity(valid_activity)

    assert result[0]["repayment_status"] == status


def test_activity_numeric_conversion(valid_activity):
    valid_activity.loc[0, "bill_amount"] = 1250.50
    valid_activity.loc[0, "payment_amount"] = 500.25
    valid_activity.loc[0, "repayment_status"] = 2

    result = validate_monthly_activity(valid_activity)

    assert result[0]["bill_amount"] == 1250.50
    assert result[0]["payment_amount"] == 500.25
    assert result[0]["repayment_status"] == 2


def test_activity_output_schema(valid_activity):
    result = validate_monthly_activity(valid_activity)

    for row in result:
        assert set(row) == {
            "activity_month",
            "repayment_status",
            "bill_amount",
            "payment_amount",
        }
