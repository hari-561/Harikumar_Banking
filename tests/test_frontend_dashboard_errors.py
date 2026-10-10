
from contextlib import nullcontext
from unittest.mock import patch

import pytest

from src.frontend.pages import (
    overview,
    risk_analysis,
    portfolio_analytics,
)


@pytest.fixture
def overview_ui():
    with (
        patch.object(
            overview.st, "columns",
            side_effect=lambda count, **kwargs:
                tuple(
                    nullcontext()
                    for _ in range(
                        count if isinstance(count, int)
                        else len(count)
                    )
                ),
        ),
        patch.object(
            overview.st, "spinner",
            return_value=nullcontext(),
        ),
        patch.object(
            overview.st, "button", return_value=False
        ),
        patch.object(
            overview, "render_section_header"
        ),
        patch.object(
            overview, "render_kpi_card"
        ),
    ):
        yield


def test_overview_loads_three_datasets():
    with (
        patch.object(
            overview,
            "get_portfolio_summary",
            return_value={"total_customers": 100},
        ),
        patch.object(
            overview,
            "get_risk_distribution",
            return_value=[],
        ),
        patch.object(
            overview,
            "get_monthly_trends",
            return_value=[],
        ),
    ):
        result = overview.load_overview_data()

    assert result == (
        {"total_customers": 100},
        [],
        [],
    )


def test_overview_api_failure(overview_ui):
    with (
        patch.object(
            overview,
            "load_overview_data",
            side_effect=overview.APIClientError(
                "Backend unavailable"
            ),
        ),
        patch.object(
            overview, "render_api_error"
        ) as show_error,
    ):
        overview.render_overview()

    show_error.assert_called_once()


@pytest.fixture
def summary():
    return {
        "total_customers": 100,
        "historical_defaults": 20,
        "historical_default_rate_pct": 20.0,
        "customers_with_payment_delay": 30,
        "average_credit_limit": 150000,
        "average_latest_utilization_pct": 45.0,
        "customers_with_repeated_delay": 10,
    }


@pytest.mark.parametrize(
    "distribution,expected_message",
    [
        (
            {"risk_band": "HIGH"},
            "unexpected format",
        ),
        (
            [],
            "No risk distribution data",
        ),
        (
            [{"risk_band": "HIGH"}],
            "incomplete",
        ),
    ],
)
def test_overview_invalid_risk_distribution(
    overview_ui,
    summary,
    distribution,
    expected_message,
):
    with (
        patch.object(
            overview,
            "load_overview_data",
            return_value=(summary, distribution, []),
        ),
        patch.object(
            overview.st, "warning"
        ) as warning,
        patch.object(
            overview.st, "info"
        ) as info,
    ):
        overview.render_overview()

    messages = [
        str(call)
        for call in (
            warning.call_args_list + info.call_args_list
        )
    ]

    assert any(
        expected_message in message
        for message in messages
    )


@pytest.fixture
def risk_ui():
    with (
        patch.object(
            risk_analysis.st,
            "spinner",
            return_value=nullcontext(),
        ),
        patch.object(
            risk_analysis, "render_section_header"
        ),
        patch.object(
            risk_analysis, "render_kpi_card"
        ),
    ):
        yield


def test_risk_analysis_api_failure(risk_ui):
    with (
        patch.object(
            risk_analysis,
            "get_risk_distribution",
            side_effect=risk_analysis.APIClientError(
                "API failed"
            ),
        ),
        patch.object(
            risk_analysis, "render_api_error"
        ) as show_error,
    ):
        risk_analysis.render_risk_analysis()

    show_error.assert_called_once()


@pytest.mark.parametrize(
    "invalid_data",
    [
        None,
        {},
        [],
        [{"risk_band": "HIGH"}],
        [
            {"risk_band": "LOW", "total_customers": 0},
            {"risk_band": "MEDIUM", "total_customers": 0},
            {"risk_band": "HIGH", "total_customers": 0},
        ],
    ],
)
def test_risk_analysis_rejects_invalid_data(
    risk_ui, invalid_data
):
    with (
        patch.object(
            risk_analysis,
            "get_risk_distribution",
            return_value=invalid_data,
        ),
        patch.object(
            risk_analysis.st, "error"
        ) as show_error,
    ):
        risk_analysis.render_risk_analysis()

    assert show_error.called
    assert "Invalid risk distribution data" in (
        show_error.call_args.args[0]
    )


@pytest.fixture
def segment():
    return {
        "segment": "University",
        "total_customers": 100,
        "average_credit_limit": 150000,
        "historical_defaults": 20,
        "historical_default_rate_pct": 20.0,
        "customers_with_payment_delay": 30,
        "average_latest_utilization_pct": 45.0,
    }


def test_valid_segment_data(segment):
    result = portfolio_analytics.validate_segment_data(
        [segment]
    )

    assert result == [segment]


@pytest.mark.parametrize(
    "invalid_data",
    [
        None,
        {},
        [],
        "invalid",
        [123],
    ],
)
def test_segment_validator_rejects_invalid_structure(
    invalid_data,
):
    with pytest.raises(ValueError):
        portfolio_analytics.validate_segment_data(
            invalid_data
        )


def test_segment_validator_missing_field(segment):
    segment.pop("historical_defaults")

    with pytest.raises(
        ValueError, match="Missing segment fields"
    ):
        portfolio_analytics.validate_segment_data(
            [segment]
        )


def test_segment_validator_duplicate_labels(segment):
    with pytest.raises(
        ValueError, match="Duplicate segment labels"
    ):
        portfolio_analytics.validate_segment_data(
            [segment, dict(segment)]
        )


@pytest.mark.parametrize(
    "count,defaults",
    [
        (-1, 0),
        (10, -1),
        (10, 11),
        (True, 0),
        (10, False),
    ],
)
def test_segment_validator_invalid_counts(
    segment, count, defaults
):
    segment["total_customers"] = count
    segment["historical_defaults"] = defaults

    with pytest.raises(ValueError):
        portfolio_analytics.validate_segment_data(
            [segment]
        )


@pytest.mark.parametrize(
    "rate",
    [-1, 101],
)
def test_segment_validator_invalid_default_rate(
    segment, rate
):
    segment["historical_default_rate_pct"] = rate

    with pytest.raises(ValueError):
        portfolio_analytics.validate_segment_data(
            [segment]
        )
