
import sys
from datetime import date
from pathlib import Path
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest
from pandas.testing import assert_frame_equal

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "etl"))

import load as db


@pytest.fixture
def customers():
    return pd.DataFrame({
        "customer_id": [1, 2],
        "gender_code": [1, 2],
        "education_code": [2, 1],
        "marital_status_code": [1, 2],
        "age": [30, 35],
    })


@pytest.fixture
def profiles():
    return pd.DataFrame({
        "customer_id": [1, 2],
        "credit_limit": [100000, 200000],
        "delay_month_count": [0, 2],
        "max_delay_status": [0, 3],
        "has_payment_delay": [False, True],
        "total_bill_amount_6m": [60000, 120000],
        "average_bill_amount_6m": [10000, 20000],
        "total_payment_amount_6m": [12000, 24000],
        "average_payment_amount_6m": [2000, 4000],
        "latest_utilization_ratio": [0.1, 0.2],
        "default_next_month": [0, 1],
    })


@pytest.fixture
def monthly():
    rows = []
    for customer_id in (1, 2):
        for month in range(4, 10):
            rows.append({
                "customer_id": customer_id,
                "activity_month": pd.Timestamp(
                    year=2005, month=month, day=1
                ),
                "repayment_status": 0,
                "bill_amount": customer_id * 1000,
                "payment_amount": customer_id * 100,
            })
    return pd.DataFrame(rows)


@pytest.fixture
def risk_data():
    return pd.DataFrame({
        "customer_id": [1, 2],
        "payment_to_bill_ratio": [0.5, float("nan")],
        "delay_frequency_score": [10, 20],
        "delay_severity_score": [5, 15],
        "utilization_score": [10, 30],
        "payment_behavior_score": [5, 10],
        "risk_score": [30, 75],
        "risk_band": ["LOW", "HIGH"],
        "rule_version": ["1.0", "1.0"],
    })


@pytest.fixture
def cursor():
    return MagicMock()


@pytest.fixture
def connection():
    conn = MagicMock()
    conn.is_connected.return_value = True
    return conn


def test_customer_upsert_sql(cursor, customers):
    db.load_customers(cursor, customers)

    cursor.executemany.assert_called_once()
    sql, records = cursor.executemany.call_args.args

    assert "INSERT INTO customers" in sql
    assert "ON DUPLICATE KEY UPDATE" in sql
    assert "gender_code = VALUES(gender_code)" in sql
    assert len(records) == 2
    assert records[0] == (1, 1, 2, 1, 30)


def test_customer_empty_dataframe(cursor, customers):
    db.load_customers(cursor, customers.iloc[0:0])

    records = cursor.executemany.call_args.args[1]
    assert records == []


def test_credit_profile_upsert(cursor, profiles):
    db.load_credit_profiles(cursor, profiles)

    sql, records = cursor.executemany.call_args.args

    assert "INSERT INTO credit_profiles" in sql
    assert "ON DUPLICATE KEY UPDATE" in sql
    assert "latest_utilization_ratio" in sql
    assert len(records) == 2
    assert len(records[0]) == 11
    assert records[1][0] == 2


def test_credit_profile_values(cursor, profiles):
    db.load_credit_profiles(cursor, profiles)

    records = cursor.executemany.call_args.args[1]

    assert records[0][1] == 100000
    assert records[0][2] == 0
    assert records[1][10] == 1


@pytest.mark.parametrize(
    "batch_size, expected_batches",
    [
        (1, 12),
        (2, 6),
        (5, 3),
        (6, 2),
        (12, 1),
        (20, 1),
    ],
)
def test_monthly_activity_batching(
    cursor, monthly, batch_size, expected_batches
):
    db.load_monthly_activity(
        cursor, monthly, batch_size=batch_size
    )

    assert cursor.executemany.call_count == expected_batches

    all_records = []
    for call in cursor.executemany.call_args_list:
        all_records.extend(call.args[1])

    assert len(all_records) == 12


def test_monthly_activity_date_conversion(cursor, monthly):
    db.load_monthly_activity(cursor, monthly)

    records = cursor.executemany.call_args.args[1]

    assert all(
        isinstance(record[1], date)
        for record in records
    )
    assert records[0][1] == date(2005, 4, 1)


def test_monthly_activity_upsert_sql(cursor, monthly):
    db.load_monthly_activity(cursor, monthly)

    sql = cursor.executemany.call_args.args[0]

    assert "INSERT INTO monthly_credit_activity" in sql
    assert "ON DUPLICATE KEY UPDATE" in sql
    assert "bill_amount = VALUES(bill_amount)" in sql


def test_monthly_activity_input_unchanged(cursor, monthly):
    original = monthly.copy(deep=True)

    db.load_monthly_activity(cursor, monthly)

    assert_frame_equal(monthly, original)


def test_monthly_activity_empty(cursor, monthly):
    db.load_monthly_activity(cursor, monthly.iloc[0:0])

    cursor.executemany.assert_not_called()


def test_database_counts(cursor):
    cursor.fetchone.side_effect = [
        (30000,),
        (30000,),
        (180000,),
    ]

    counts = db.get_database_counts(cursor)

    assert counts == {
        "customers": 30000,
        "credit_profiles": 30000,
        "monthly_credit_activity": 180000,
    }
    assert cursor.execute.call_count == 3


def test_database_count_queries(cursor):
    cursor.fetchone.side_effect = [(2,), (2,), (12,)]

    db.get_database_counts(cursor)

    queries = [
        call.args[0]
        for call in cursor.execute.call_args_list
    ]

    assert queries == [
        "SELECT COUNT(*) FROM customers",
        "SELECT COUNT(*) FROM credit_profiles",
        "SELECT COUNT(*) FROM monthly_credit_activity",
    ]


def test_risk_assessment_upsert(cursor, risk_data):
    db.load_risk_assessments(cursor, risk_data)

    sql, records = cursor.executemany.call_args.args

    assert "INSERT INTO customer_risk_assessment" in sql
    assert "ON DUPLICATE KEY UPDATE" in sql
    assert len(records) == 2
    assert len(records[0]) == 9
    assert records[0][0] == 1
    assert records[0][7] == "LOW"
    assert records[0][8] == "1.0"


def test_risk_assessment_null_ratio(cursor, risk_data):
    db.load_risk_assessments(cursor, risk_data)

    records = cursor.executemany.call_args.args[1]

    assert records[0][1] == 0.5
    assert records[1][1] is None


def test_risk_assessment_empty(cursor, risk_data):
    db.load_risk_assessments(
        cursor, risk_data.iloc[0:0]
    )

    cursor.executemany.assert_not_called()


def test_get_connection_success(connection):
    with patch.object(
        db.mysql.connector,
        "connect",
        return_value=connection,
    ) as connect_mock:
        result = db.get_connection()

    assert result is connection
    connect_mock.assert_called_once_with(**db.DB_CONFIG)


def test_get_connection_failure():
    with patch.object(
        db.mysql.connector,
        "connect",
        side_effect=db.Error("Mock connection failure"),
    ):
        with pytest.raises(
            ConnectionError,
            match="Unable to connect to MySQL",
        ):
            db.get_connection()


def test_load_database_success(
    customers, profiles, monthly, connection
):
    cursor = connection.cursor.return_value

    with (
        patch.object(
            db, "get_connection",
            return_value=connection,
        ),
        patch.object(db, "get_database_counts", return_value={
            "customers": 2,
            "credit_profiles": 2,
            "monthly_credit_activity": 12,
        }),
    ):
        counts = db.load_database(
            customers, profiles, monthly
        )

    assert counts["customers"] == 2
    assert counts["monthly_credit_activity"] == 12

    assert cursor.executemany.call_count == 3
    connection.commit.assert_called_once()
    connection.rollback.assert_not_called()
    cursor.close.assert_called_once()
    connection.close.assert_called_once()


@pytest.mark.parametrize(
    "failing_loader",
    [
        "load_customers",
        "load_credit_profiles",
        "load_monthly_activity",
    ],
)
def test_load_database_rolls_back(
    customers, profiles, monthly, connection, failing_loader
):
    with (
        patch.object(
            db, "get_connection",
            return_value=connection,
        ),
        patch.object(
            db, failing_loader,
            side_effect=RuntimeError("Mock insert failure"),
        ),
    ):
        with pytest.raises(
            RuntimeError,
            match="Database load failed",
        ):
            db.load_database(customers, profiles, monthly)

    connection.rollback.assert_called_once()
    connection.commit.assert_not_called()
    connection.close.assert_called_once()


def test_load_database_closes_connection(
    customers, profiles, monthly, connection
):
    with (
        patch.object(
            db, "get_connection",
            return_value=connection,
        ),
        patch.object(
            db, "get_database_counts",
            return_value={
                "customers": 2,
                "credit_profiles": 2,
                "monthly_credit_activity": 12,
            },
        ),
    ):
        db.load_database(customers, profiles, monthly)

    connection.cursor.return_value.close.assert_called_once()
    connection.close.assert_called_once()
