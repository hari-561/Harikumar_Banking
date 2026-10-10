
import sys
from pathlib import Path

import pandas as pd
import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "etl"))

from validate import (
    BILL_COLUMNS,
    PAYMENT_COLUMNS,
    REPAYMENT_COLUMNS,
    TARGET_COLUMN,
    validate_data,
    validation_passed,
)


@pytest.fixture
def valid_data():
    """Create two valid banking records."""

    records = []

    for customer_id in (1, 2):
        row = {
            "ID": customer_id,
            "LIMIT_BAL": 100000,
            "SEX": 1,
            "EDUCATION": 2,
            "MARRIAGE": 1,
            "AGE": 30,
            TARGET_COLUMN: 0,
        }

        for column in REPAYMENT_COLUMNS:
            row[column] = 0

        for column in BILL_COLUMNS:
            row[column] = 10000

        for column in PAYMENT_COLUMNS:
            row[column] = 2000

        records.append(row)

    return pd.DataFrame(records)


def get_result(report, check):
    """Return the status and count of a specific DQ check."""

    matches = report.loc[report["check"] == check]

    assert len(matches) == 1, (
        f"Expected exactly one result for {check}"
    )

    result = matches.iloc[0]

    return result["status"], int(result["count"])


def test_valid_dataset_passes_all_checks(valid_data):
    report = validate_data(valid_data)

    assert len(report) == 13
    assert set(report["status"]) == {"PASS"}
    assert report["count"].sum() == 0
    assert validation_passed(report) is True


def test_report_schema(valid_data):
    report = validate_data(valid_data)

    assert list(report.columns) == [
        "check",
        "status",
        "count",
        "message",
    ]

    assert report["check"].is_unique
    assert len(report) == 13


def test_missing_values_fail(valid_data):
    df = valid_data.copy()
    df.loc[0, "AGE"] = None

    report = validate_data(df)

    assert get_result(
        report, "DQ01_MISSING_VALUES"
    ) == ("FAIL", 1)

    assert validation_passed(report) is False


def test_missing_customer_id_fail(valid_data):
    df = valid_data.copy()
    df.loc[0, "ID"] = None

    report = validate_data(df)

    assert get_result(
        report, "DQ03_MISSING_CUSTOMER_ID"
    ) == ("FAIL", 1)


def test_duplicate_complete_rows_fail(valid_data):
    df = pd.concat(
        [valid_data, valid_data.iloc[[0]]],
        ignore_index=True,
    )

    report = validate_data(df)

    assert get_result(
        report, "DQ02_DUPLICATE_ROWS"
    ) == ("FAIL", 1)


def test_duplicate_customer_id_fail(valid_data):
    df = valid_data.copy()
    df.loc[1, "ID"] = 1

    # Keep rows different so DQ04 is tested independently.
    df.loc[1, "AGE"] = 35

    report = validate_data(df)

    assert get_result(
        report, "DQ04_DUPLICATE_CUSTOMER_ID"
    ) == ("FAIL", 1)


@pytest.mark.parametrize("credit_limit", [0, -1000])
def test_invalid_credit_limit_fail(valid_data, credit_limit):
    df = valid_data.copy()
    df.loc[0, "LIMIT_BAL"] = credit_limit

    report = validate_data(df)

    assert get_result(
        report, "DQ05_INVALID_CREDIT_LIMIT"
    ) == ("FAIL", 1)


@pytest.mark.parametrize("gender", [0, 3, 9])
def test_invalid_gender_fail(valid_data, gender):
    df = valid_data.copy()
    df.loc[0, "SEX"] = gender

    report = validate_data(df)

    assert get_result(
        report, "DQ06_INVALID_GENDER"
    ) == ("FAIL", 1)


@pytest.mark.parametrize("education", [0, 5, 6])
def test_undocumented_education_warns(valid_data, education):
    df = valid_data.copy()
    df.loc[0, "EDUCATION"] = education

    report = validate_data(df)

    assert get_result(
        report, "DQ07_UNDOCUMENTED_EDUCATION"
    ) == ("WARNING", 1)

    assert validation_passed(report) is True


@pytest.mark.parametrize("marriage", [0, 4])
def test_undocumented_marriage_warns(valid_data, marriage):
    df = valid_data.copy()
    df.loc[0, "MARRIAGE"] = marriage

    report = validate_data(df)

    assert get_result(
        report, "DQ08_UNDOCUMENTED_MARRIAGE"
    ) == ("WARNING", 1)

    assert validation_passed(report) is True


@pytest.mark.parametrize("age", [0, -5])
def test_invalid_age_fail(valid_data, age):
    df = valid_data.copy()
    df.loc[0, "AGE"] = age

    report = validate_data(df)

    assert get_result(
        report, "DQ09_INVALID_AGE"
    ) == ("FAIL", 1)


@pytest.mark.parametrize("repayment_status", [-3, 9])
def test_invalid_repayment_status_fail(
    valid_data, repayment_status
):
    df = valid_data.copy()
    df.loc[0, "PAY_0"] = repayment_status

    report = validate_data(df)

    assert get_result(
        report, "DQ10_INVALID_REPAYMENT_STATUS"
    ) == ("FAIL", 1)


@pytest.mark.parametrize("repayment_status", [-2, -1, 0, 8])
def test_valid_repayment_boundaries(
    valid_data, repayment_status
):
    df = valid_data.copy()
    df.loc[0, "PAY_0"] = repayment_status

    report = validate_data(df)

    assert get_result(
        report, "DQ10_INVALID_REPAYMENT_STATUS"
    ) == ("PASS", 0)


def test_negative_bill_balance_warns(valid_data):
    df = valid_data.copy()
    df.loc[0, "BILL_AMT1"] = -500

    report = validate_data(df)

    assert get_result(
        report, "DQ11_NEGATIVE_BILL_BALANCE"
    ) == ("WARNING", 1)

    assert validation_passed(report) is True


def test_negative_payment_fails(valid_data):
    df = valid_data.copy()
    df.loc[0, "PAY_AMT1"] = -100

    report = validate_data(df)

    assert get_result(
        report, "DQ12_NEGATIVE_PAYMENT"
    ) == ("FAIL", 1)

    assert validation_passed(report) is False


@pytest.mark.parametrize("target", [-1, 2])
def test_invalid_default_target_fails(valid_data, target):
    df = valid_data.copy()
    df.loc[0, TARGET_COLUMN] = target

    report = validate_data(df)

    assert get_result(
        report, "DQ13_INVALID_DEFAULT_TARGET"
    ) == ("FAIL", 1)


def test_multiple_invalid_values_are_counted(valid_data):
    df = valid_data.copy()

    df.loc[0, "PAY_AMT1"] = -100
    df.loc[0, "PAY_AMT2"] = -200
    df.loc[1, "PAY_AMT3"] = -300

    report = validate_data(df)

    assert get_result(
        report, "DQ12_NEGATIVE_PAYMENT"
    ) == ("FAIL", 3)


def test_warnings_do_not_block_pipeline(valid_data):
    df = valid_data.copy()

    df.loc[0, "EDUCATION"] = 5
    df.loc[1, "MARRIAGE"] = 0
    df.loc[0, "BILL_AMT1"] = -100

    report = validate_data(df)

    assert (report["status"] == "WARNING").sum() == 3
    assert (report["status"] == "FAIL").sum() == 0

    assert validation_passed(report) is True


def test_failure_blocks_pipeline(valid_data):
    df = valid_data.copy()

    df.loc[0, "EDUCATION"] = 5
    df.loc[1, "LIMIT_BAL"] = 0

    report = validate_data(df)

    assert (report["status"] == "WARNING").sum() == 1
    assert (report["status"] == "FAIL").sum() == 1

    assert validation_passed(report) is False
