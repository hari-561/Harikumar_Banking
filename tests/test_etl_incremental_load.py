
import sys
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "etl"))

import incremental_load as pipeline


@pytest.fixture
def customer_data():
    """Minimal transformed dataset for transaction tests."""
    return pd.DataFrame({
        "customer_id": [1, 2, 3],
        "credit_limit": [100000, 200000, 300000],
    })


@pytest.fixture
def mock_connection():
    connection = MagicMock()
    connection.is_connected.return_value = True
    connection.cursor.return_value.lastrowid = 42
    return connection


@pytest.fixture
def pipeline_mocks(customer_data, mock_connection):
    """Mock every external dependency of the pipeline."""
    patches = [
        patch.object(
            pipeline, "extract_data",
            return_value=customer_data.copy(),
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
            return_value=customer_data.copy(),
        ),
        patch.object(
            pipeline, "fetch_existing_customers",
            return_value=customer_data.copy(),
        ),
        patch.object(
            pipeline, "get_connection",
            return_value=mock_connection,
        ),
        patch.object(
            pipeline, "prepare_database_tables",
            side_effect=lambda df: (
                df.copy(), df.copy(), df.copy()
            ),
        ),
        patch.object(pipeline, "load_customers"),
        patch.object(pipeline, "load_credit_profiles"),
        patch.object(pipeline, "load_monthly_activity"),
    ]

    mocks = [item.start() for item in patches]

    yield {
        "extract": mocks[0],
        "validate": mocks[1],
        "validation_passed": mocks[2],
        "transform": mocks[3],
        "fetch": mocks[4],
        "get_connection": mocks[5],
        "prepare": mocks[6],
        "load_customers": mocks[7],
        "load_profiles": mocks[8],
        "load_monthly": mocks[9],
        "connection": mock_connection,
    }

    for item in reversed(patches):
        item.stop()


def set_classification(mocks, new_ids, changed_ids, unchanged_ids):
    """Return comparison-level customer records by ID."""
    source = mocks["transform"].return_value

    def select(ids):
        return source[
            source["customer_id"].isin(ids)
        ].copy()

    classification = (
        select(new_ids),
        select(changed_ids),
        select(unchanged_ids),
    )

    return classification


def test_create_audit_record(mock_connection):
    cursor = mock_connection.cursor.return_value

    result = pipeline.create_audit_record(
        mock_connection,
        r"D:\banking_loan\data\incoming.xls",
        datetime(2026, 10, 10, 10, 0),
        30000,
    )

    assert result == 42

    query, parameters = cursor.execute.call_args.args

    assert "INSERT INTO etl_batch_audit" in query
    assert parameters[0] == "incoming.xls"
    assert parameters[2] == 30000
    assert parameters[3] == "RUNNING"

    cursor.close.assert_called_once()


def test_complete_audit_record(mock_connection):
    pipeline.complete_audit_record(
        mock_connection,
        batch_id=42,
        new_count=1,
        updated_count=2,
        unchanged_count=7,
        loaded_count=3,
    )

    cursor = mock_connection.cursor.return_value
    query, parameters = cursor.execute.call_args.args

    assert "UPDATE etl_batch_audit" in query
    assert "status = 'SUCCESS'" in query
    assert "failed_record_count = 0" in query

    assert parameters[1:] == (1, 2, 7, 3, 42)

    cursor.close.assert_called_once()


def test_fail_audit_record(mock_connection):
    pipeline.fail_audit_record(
        mock_connection,
        batch_id=42,
        error_message="Mock database failure",
    )

    cursor = mock_connection.cursor.return_value
    query, parameters = cursor.execute.call_args.args

    assert "UPDATE etl_batch_audit" in query
    assert "status = 'FAILED'" in query
    assert parameters[1] == "Mock database failure"
    assert parameters[2] == 42


def test_failure_message_truncated(mock_connection):
    pipeline.fail_audit_record(
        mock_connection,
        batch_id=42,
        error_message="X" * 6000,
    )

    cursor = mock_connection.cursor.return_value
    parameters = cursor.execute.call_args.args[1]

    assert len(parameters[1]) == 5000


def test_pipeline_no_changes(pipeline_mocks):
    mocks = pipeline_mocks

    classification = set_classification(
        mocks, [], [], [1, 2, 3]
    )

    with patch.object(
        pipeline, "detect_changes",
        return_value=classification,
    ):
        pipeline.run_incremental_pipeline("incoming.xls")

    connection = mocks["connection"]

    connection.start_transaction.assert_called_once()
    connection.commit.assert_called_once()
    connection.rollback.assert_not_called()

    mocks["prepare"].assert_not_called()
    mocks["load_customers"].assert_not_called()
    mocks["load_profiles"].assert_not_called()
    mocks["load_monthly"].assert_not_called()

    cursor = connection.cursor.return_value
    queries = [
        call.args[0]
        for call in cursor.execute.call_args_list
    ]

    assert any("status = 'SUCCESS'" in q for q in queries)


def test_pipeline_new_customer(pipeline_mocks):
    mocks = pipeline_mocks

    classification = set_classification(
        mocks, [1], [], [2, 3]
    )

    with patch.object(
        pipeline, "detect_changes",
        return_value=classification,
    ):
        pipeline.run_incremental_pipeline("incoming.xls")

    prepared_data = mocks["prepare"].call_args.args[0]

    assert prepared_data["customer_id"].tolist() == [1]

    mocks["load_customers"].assert_called_once()
    mocks["load_profiles"].assert_called_once()
    mocks["load_monthly"].assert_called_once()

    mocks["connection"].commit.assert_called_once()


def test_pipeline_changed_customer(pipeline_mocks):
    mocks = pipeline_mocks

    classification = set_classification(
        mocks, [], [2], [1, 3]
    )

    with patch.object(
        pipeline, "detect_changes",
        return_value=classification,
    ):
        pipeline.run_incremental_pipeline("incoming.xls")

    prepared_data = mocks["prepare"].call_args.args[0]

    assert prepared_data["customer_id"].tolist() == [2]

    mocks["connection"].commit.assert_called_once()


def test_pipeline_mixed_changes(pipeline_mocks):
    mocks = pipeline_mocks

    classification = set_classification(
        mocks, [1], [2], [3]
    )

    with patch.object(
        pipeline, "detect_changes",
        return_value=classification,
    ):
        pipeline.run_incremental_pipeline("incoming.xls")

    prepared_data = mocks["prepare"].call_args.args[0]

    assert set(prepared_data["customer_id"]) == {1, 2}
    assert len(prepared_data) == 2

    cursor = mocks["connection"].cursor.return_value

    success_calls = [
        call for call in cursor.execute.call_args_list
        if "status = 'SUCCESS'" in call.args[0]
    ]

    assert len(success_calls) == 1

    parameters = success_calls[0].args[1]
    assert parameters[1:5] == (1, 1, 1, 2)


def test_pipeline_classification_failure(pipeline_mocks):
    mocks = pipeline_mocks

    classification = set_classification(
        mocks, [1], [], [2]
    )

    with patch.object(
        pipeline, "detect_changes",
        return_value=classification,
    ):
        with pytest.raises(
            RuntimeError,
            match="classification reconciliation failed",
        ):
            pipeline.run_incremental_pipeline("incoming.xls")

    mocks["get_connection"].assert_not_called()


def test_pipeline_load_reconciliation_failure(pipeline_mocks):
    mocks = pipeline_mocks

    # Customer 1 is incorrectly present in both categories.
    classification = set_classification(
        mocks, [1], [1], [2]
    )

    with patch.object(
        pipeline, "detect_changes",
        return_value=classification,
    ):
        with pytest.raises(
            RuntimeError,
            match="load reconciliation failed",
        ):
            pipeline.run_incremental_pipeline("incoming.xls")

    mocks["get_connection"].assert_not_called()


def test_pipeline_validation_failure(pipeline_mocks):
    mocks = pipeline_mocks

    mocks["validation_passed"].return_value = False

    with pytest.raises(
        ValueError,
        match="Source dataset failed validation",
    ):
        pipeline.run_incremental_pipeline("incoming.xls")

    mocks["transform"].assert_not_called()
    mocks["get_connection"].assert_not_called()


def test_pipeline_load_error_rolls_back(pipeline_mocks):
    mocks = pipeline_mocks

    classification = set_classification(
        mocks, [1], [], [2, 3]
    )

    mocks["load_profiles"].side_effect = RuntimeError(
        "Mock profile load failure"
    )

    # First connection: main transaction.
    # Second connection: independent failure audit.
    main_connection = mocks["connection"]

    failure_connection = MagicMock()
    failure_connection.is_connected.return_value = True

    mocks["get_connection"].side_effect = [
        main_connection,
        failure_connection,
    ]

    with patch.object(
        pipeline, "detect_changes",
        return_value=classification,
    ):
        with pytest.raises(
            RuntimeError,
            match="Mock profile load failure",
        ):
            pipeline.run_incremental_pipeline("incoming.xls")

    main_connection.rollback.assert_called_once()
    main_connection.commit.assert_not_called()

    failure_connection.commit.assert_called_once()

    failure_cursor = failure_connection.cursor.return_value
    query, parameters = failure_cursor.execute.call_args.args

    assert "INSERT INTO etl_batch_audit" in query
    assert parameters[-2] == "FAILED"
    assert "Mock profile load failure" in parameters[-1]

    main_connection.close.assert_called_once()
    failure_connection.close.assert_called_once()


def test_pipeline_failed_load_stops_remaining_loads(
    pipeline_mocks,
):
    mocks = pipeline_mocks

    classification = set_classification(
        mocks, [1], [], [2, 3]
    )

    mocks["load_customers"].side_effect = RuntimeError(
        "Customer insert failed"
    )

    failure_connection = MagicMock()
    failure_connection.is_connected.return_value = True

    mocks["get_connection"].side_effect = [
        mocks["connection"],
        failure_connection,
    ]

    with patch.object(
        pipeline, "detect_changes",
        return_value=classification,
    ):
        with pytest.raises(
            RuntimeError,
            match="Customer insert failed",
        ):
            pipeline.run_incremental_pipeline("incoming.xls")

    mocks["load_profiles"].assert_not_called()
    mocks["load_monthly"].assert_not_called()


def test_pipeline_closes_connection_on_success(pipeline_mocks):
    mocks = pipeline_mocks

    classification = set_classification(
        mocks, [], [], [1, 2, 3]
    )

    with patch.object(
        pipeline, "detect_changes",
        return_value=classification,
    ):
        pipeline.run_incremental_pipeline("incoming.xls")

    mocks["connection"].close.assert_called_once()


def test_pipeline_extract_failure(pipeline_mocks):
    mocks = pipeline_mocks

    mocks["extract"].side_effect = FileNotFoundError(
        "Source file missing"
    )

    with pytest.raises(
        FileNotFoundError,
        match="Source file missing",
    ):
        pipeline.run_incremental_pipeline("missing.xls")

    mocks["get_connection"].assert_not_called()
