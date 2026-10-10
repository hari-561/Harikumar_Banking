import math

import pytest

from src.frontend.api_client import (
    get_portfolio_summary,
    get_risk_distribution,
    get_customer_segments,
)

@pytest.fixture
def summary(authenticated_frontend):
    return get_portfolio_summary()


@pytest.fixture
def risk_data(authenticated_frontend):
    return get_risk_distribution()


@pytest.mark.parametrize(
    "segment_type",
    [
        "gender",
        "education",
        "marital_status",
        "age",
    ],
)
def test_segment_reconciliation(
    segment_type,
    summary,
):
    segments = get_customer_segments(segment_type)

    assert isinstance(segments, list)
    assert len(segments) > 0

    total_customers = sum(
        row["total_customers"]
        for row in segments
    )

    total_defaults = sum(
        row["historical_defaults"]
        for row in segments
    )

    assert total_customers == summary["total_customers"]
    assert total_defaults == summary["historical_defaults"]

    for row in segments:
        count = row["total_customers"]
        defaults = row["historical_defaults"]

        assert count >= 0
        assert 0 <= defaults <= count

        if count > 0:
            calculated_rate = defaults / count * 100

            assert math.isclose(
                calculated_rate,
                row["historical_default_rate_pct"],
                abs_tol=0.01,
            )


def test_risk_distribution_reconciliation(
    risk_data,
    summary,
):
    assert isinstance(risk_data, list)

    assert {
        row["risk_band"]
        for row in risk_data
    } == {"LOW", "MEDIUM", "HIGH"}

    assert sum(
        row["total_customers"]
        for row in risk_data
    ) == summary["total_customers"]

    assert sum(
        row["historical_defaults"]
        for row in risk_data
    ) == summary["historical_defaults"]


def test_risk_score_ranges(risk_data):
    ranges = {
        "LOW": (0, 2),
        "MEDIUM": (3, 5),
        "HIGH": (6, 11),
    }

    for row in risk_data:
        lower, upper = ranges[row["risk_band"]]

        assert lower <= row["average_risk_score"] <= upper


def test_education_segment_values():
    segments = get_customer_segments("education")

    lookup = {
        row["segment"]: row
        for row in segments
    }

    assert lookup["University"]["total_customers"] == 14030
    assert lookup["Graduate School"]["total_customers"] == 10585
    assert lookup["High School"]["total_customers"] == 4917
    assert lookup["Others"]["total_customers"] == 468