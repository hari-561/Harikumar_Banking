
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "etl"))

import incremental as change_detection
import incremental_load as pipeline


MONTHS = ["sep", "aug", "jul", "jun", "may", "apr"]


def make_customer(customer_id, credit_limit=100000):
    """Build a complete transformed customer record."""

    row = {
        "customer_id": customer_id,
        "credit_limit": credit_limit,
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
        "latest_utilization_ratio": 0.1,
        "default_next_month": 0,
    }

    for month in MONTHS:
        row[f"repayment_status_{month}"] = 0
        row[f"bill_amount_{month}"] = 10000
        row[f"payment_amount_{month}"] = 2000

    return row


@pytest.fixture
def source_data():
    return pd.DataFrame([
        make_customer(1),
        make_customer(2),
        make_customer(3),
    ])


@pytest.fixture
def database_mocks():
    connection = MagicMock()
    connection.is_connected.return_value = True
    connection.cursor.return_value.lastrowid = 101

    with (
        patch.object(
            pipeline, "get_connection",
            return_value=connection,
        ),
        patch.object(pipeline, "load_customers") as customers_loader,
        patch.object(
            pipeline, "load_credit_profiles"
        ) as profiles_loader,
        patch.object(
            pipeline, "load_monthly_activity"
        ) as monthly_loader,
    ):
        yield {
            "connection": connection,
            "customers": customers_loader,
            "profiles": profiles_loader,
            "monthly": monthly_loader,
        }


def run_with_data(incoming, existing):
    """
    Run the actual change detection and table preparation
    through the incremental pipeline.

    Only file ingestion, validation, and database access
    are mocked.
    """

    with (
        patch.object(
            pipeline, "extract_data",
            return_value=incoming.copy(),
        ),
        patch.object(
            pipeline, "validate_data",
            return_value=[],
        ),
        patch.object(
            pipeline, "validation_passed",
            return_value=True,
        ),
        patch.object(
            pipeline, "transform_data",
            return_value=incoming.copy(),
        ),
        patch.object(
            pipeline, "fetch_existing_customers",
            return_value=existing.copy(),
        ),
    ):
        pipeline.run_incremental_pipeline("integration_test.xls")


def get_success_counts(connection):
    """Read counts passed to the successful audit update."""

    cursor = connection.cursor.return_value

    success_calls = [
        call
        for call in cursor.execute.call_args_list
        if "status = 'SUCCESS'" in call.args[0]
    ]

    assert len(success_calls) == 1

    parameters = success_calls[0].args[1]

    return {
        "new": parameters[1],
        "updated": parameters[2],
        "unchanged": parameters[3],
        "loaded": parameters[4],
    }


def test_initial_load_all_customers_new(
    source_data, database_mocks
):
    existing = source_data.iloc[0:0].copy()

    run_with_data(source_data, existing)

    assert get_success_counts(
        database_mocks["connection"]
    ) == {
        "new": 3,
        "updated": 0,
        "unchanged": 0,
        "loaded": 3,
    }

    customer_df = database_mocks[
        "customers"
    ].call_args.args[1]

    profile_df = database_mocks[
        "profiles"
    ].call_args.args[1]

    monthly_df = database_mocks[
        "monthly"
    ].call_args.args[1]

    assert len(customer_df) == 3
    assert len(profile_df) == 3
    assert len(monthly_df) == 18

    assert set(customer_df["customer_id"]) == {1, 2, 3}

    database_mocks["connection"].commit.assert_called_once()


def test_second_identical_run_skips_database_loads(
    source_data, database_mocks
):
    run_with_data(source_data, source_data.copy())

    assert get_success_counts(
        database_mocks["connection"]
    ) == {
        "new": 0,
        "updated": 0,
        "unchanged": 3,
        "loaded": 0,
    }

    database_mocks["customers"].assert_not_called()
    database_mocks["profiles"].assert_not_called()
    database_mocks["monthly"].assert_not_called()

    # The audit transaction is still committed.
    database_mocks["connection"].commit.assert_called_once()


def test_only_updated_customer_is_loaded(
    source_data, database_mocks
):
    incoming = source_data.copy()
    incoming.loc[
        incoming["customer_id"] == 2,
        "credit_limit",
    ] = 250000

    run_with_data(incoming, source_data)

    assert get_success_counts(
        database_mocks["connection"]
    ) == {
        "new": 0,
        "updated": 1,
        "unchanged": 2,
        "loaded": 1,
    }

    customer_df = database_mocks[
        "customers"
    ].call_args.args[1]

    profile_df = database_mocks[
        "profiles"
    ].call_args.args[1]

    monthly_df = database_mocks[
        "monthly"
    ].call_args.args[1]

    assert customer_df["customer_id"].tolist() == [2]
    assert profile_df["customer_id"].tolist() == [2]
    assert profile_df.iloc[0]["credit_limit"] == 250000
    assert len(monthly_df) == 6


def test_only_new_customer_is_loaded(
    source_data, database_mocks
):
    incoming = pd.concat(
        [
            source_data,
            pd.DataFrame([make_customer(4)]),
        ],
        ignore_index=True,
    )

    run_with_data(incoming, source_data)

    assert get_success_counts(
        database_mocks["connection"]
    ) == {
        "new": 1,
        "updated": 0,
        "unchanged": 3,
        "loaded": 1,
    }

    customer_df = database_mocks[
        "customers"
    ].call_args.args[1]

    monthly_df = database_mocks[
        "monthly"
    ].call_args.args[1]

    assert customer_df["customer_id"].tolist() == [4]
    assert len(monthly_df) == 6
    assert set(monthly_df["customer_id"]) == {4}


def test_mixed_new_updated_unchanged_batch(
    source_data, database_mocks
):
    incoming = source_data.copy()

    incoming.loc[
        incoming["customer_id"] == 2,
        "credit_limit",
    ] = 275000

    incoming = pd.concat(
        [
            incoming,
            pd.DataFrame([make_customer(4)]),
        ],
        ignore_index=True,
    )

    run_with_data(incoming, source_data)

    assert get_success_counts(
        database_mocks["connection"]
    ) == {
        "new": 1,
        "updated": 1,
        "unchanged": 2,
        "loaded": 2,
    }

    customer_df = database_mocks[
        "customers"
    ].call_args.args[1]

    profile_df = database_mocks[
        "profiles"
    ].call_args.args[1]

    monthly_df = database_mocks[
        "monthly"
    ].call_args.args[1]

    assert set(customer_df["customer_id"]) == {2, 4}
    assert set(profile_df["customer_id"]) == {2, 4}
    assert set(monthly_df["customer_id"]) == {2, 4}

    assert len(customer_df) == 2
    assert len(profile_df) == 2
    assert len(monthly_df) == 12


def test_monthly_activity_has_six_distinct_months(
    source_data, database_mocks
):
    existing = source_data.iloc[0:0].copy()

    run_with_data(source_data, existing)

    monthly_df = database_mocks[
        "monthly"
    ].call_args.args[1]

    for customer_id in (1, 2, 3):
        customer_months = monthly_df[
            monthly_df["customer_id"] == customer_id
        ]

        assert len(customer_months) == 6
        assert customer_months["activity_month"].nunique() == 6


def test_comparison_ignores_insignificant_decimal_difference(
    source_data, database_mocks
):
    incoming = source_data.copy()

    incoming.loc[
        incoming["customer_id"] == 1,
        "latest_utilization_ratio",
    ] = 0.1000001

    run_with_data(incoming, source_data)

    counts = get_success_counts(
        database_mocks["connection"]
    )

    assert counts["updated"] == 0
    assert counts["unchanged"] == 3
    assert counts["loaded"] == 0

    database_mocks["customers"].assert_not_called()


def test_real_change_detection_reconciles_counts(source_data):
    incoming = source_data.copy()

    incoming.loc[
        incoming["customer_id"] == 2,
        "credit_limit",
    ] = 250000

    incoming = pd.concat(
        [
            incoming,
            pd.DataFrame([make_customer(4)]),
        ],
        ignore_index=True,
    )

    new, changed, unchanged = change_detection.detect_changes(
        incoming, source_data
    )

    assert len(new) == 1
    assert len(changed) == 1
    assert len(unchanged) == 2

    assert (
        len(new) + len(changed) + len(unchanged)
        == len(incoming)
    )
