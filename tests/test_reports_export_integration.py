
import csv
from io import StringIO

import pytest
import requests


BASE_URL = "http://127.0.0.1:8000"

EXPECTED_CUSTOMERS = 30000
EXPECTED_DEFAULTS = 6636
EXPECTED_DELAYS = 10069

EXPECTED_RISK_COUNTS = {
    "LOW": 13966,
    "MEDIUM": 9673,
    "HIGH": 6361,
}

SEGMENTS = [
    "gender",
    "education",
    "marital_status",
    "age",
]


import os


@pytest.fixture(scope="module")
def session():
    username = os.getenv("TEST_API_USERNAME")
    password = os.getenv("TEST_API_PASSWORD")

    if not username or not password:
        pytest.fail(
            "Set TEST_API_USERNAME and TEST_API_PASSWORD "
            "before running integration tests."
        )

    with requests.Session() as client:
        login_response = client.post(
            f"{BASE_URL}/auth/login",
            json={
                "username": username,
                "password": password,
            },
            timeout=30,
        )

        assert login_response.status_code == 200, (
            "Integration test login failed: "
            f"HTTP {login_response.status_code}"
        )

        token = login_response.json()["access_token"]

        client.headers.update({
            "Authorization": f"Bearer {token}"
        })

        yield client


def get_json(session, endpoint, params=None):
    response = session.get(
        f"{BASE_URL}{endpoint}",
        params=params,
        timeout=60,
    )
    assert response.status_code == 200, response.text
    return response.json()


def get_csv_rows(session, params=None):
    response = session.get(
        f"{BASE_URL}/export/customers",
        params=params,
        timeout=120,
    )

    assert response.status_code == 200, response.text
    assert "text/csv" in response.headers.get(
        "content-type", ""
    ).lower()

    reader = csv.DictReader(
        StringIO(response.content.decode("utf-8-sig"))
    )

    rows = list(reader)
    return reader.fieldnames, rows


def test_portfolio_summary(session):
    data = get_json(session, "/analytics/summary")

    assert data["total_customers"] == EXPECTED_CUSTOMERS
    assert data["historical_defaults"] == EXPECTED_DEFAULTS
    assert (
        data["customers_with_payment_delay"]
        == EXPECTED_DELAYS
    )
    assert data["total_credit_exposure"] == 5024529680


def test_risk_distribution(session):
    data = get_json(
        session,
        "/analytics/risk-distribution",
    )

    actual = {
        row["risk_band"]: row["total_customers"]
        for row in data
    }

    assert actual == EXPECTED_RISK_COUNTS

    assert sum(
        row["historical_defaults"]
        for row in data
    ) == EXPECTED_DEFAULTS


@pytest.mark.parametrize("segment", SEGMENTS)
def test_segment_analytics(session, segment):
    data = get_json(
        session,
        "/analytics/segments",
        params={"segment": segment},
    )

    assert isinstance(data, list)
    assert len(data) > 0

    assert sum(
        row["total_customers"]
        for row in data
    ) == EXPECTED_CUSTOMERS

    assert sum(
        row["historical_defaults"]
        for row in data
    ) == EXPECTED_DEFAULTS

    assert sum(
        row["customers_with_payment_delay"]
        for row in data
    ) == EXPECTED_DELAYS


def test_export_all_customers(session):
    columns, rows = get_csv_rows(session)

    assert len(rows) == EXPECTED_CUSTOMERS
    assert len(columns) == 18

    required_columns = {
        "customer_id",
        "credit_limit",
        "risk_score",
        "risk_band",
        "has_payment_delay",
    }

    assert required_columns.issubset(set(columns))


@pytest.mark.parametrize(
    "risk_band,expected_count",
    [
        ("LOW", 13966),
        ("MEDIUM", 9673),
        ("HIGH", 6361),
    ],
)
def test_export_risk_filter(
    session,
    risk_band,
    expected_count,
):
    _, rows = get_csv_rows(
        session,
        params={"risk_band": risk_band},
    )

    assert len(rows) == expected_count

    assert all(
        row["risk_band"] == risk_band
        for row in rows
    )


@pytest.mark.parametrize(
    "has_delay,expected_count",
    [
        (True, 10069),
        (False, 19931),
    ],
)
def test_export_payment_delay_filter(
    session,
    has_delay,
    expected_count,
):
    _, rows = get_csv_rows(
        session,
        params={"has_payment_delay": has_delay},
    )

    assert len(rows) == expected_count

    expected_value = str(has_delay)

    assert all(
        row["has_payment_delay"] == expected_value
        for row in rows
    )


def test_export_credit_limit_filter(session):
    _, rows = get_csv_rows(
        session,
        params={
            "min_credit_limit": 100000,
            "max_credit_limit": 200000,
        },
    )

    assert len(rows) > 0

    assert all(
        100000 <= float(row["credit_limit"]) <= 200000
        for row in rows
    )


def test_export_sorting(session):
    _, rows = get_csv_rows(
        session,
        params={
            "risk_band": "HIGH",
            "sort_by": "risk_score",
            "sort_order": "desc",
        },
    )

    scores = [
        int(row["risk_score"])
        for row in rows
    ]

    assert scores == sorted(scores, reverse=True)


def test_export_has_no_database_side_effects(session):
    before = get_json(
        session,
        "/analytics/summary",
    )

    response = session.get(
        f"{BASE_URL}/export/customers",
        params={"risk_band": "HIGH"},
        timeout=120,
    )

    assert response.status_code == 200

    after = get_json(
        session,
        "/analytics/summary",
    )

    assert before == after
