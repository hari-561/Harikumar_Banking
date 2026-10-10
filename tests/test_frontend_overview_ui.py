
from contextlib import nullcontext
from unittest.mock import patch

import pytest

from src.frontend.pages import overview


SUMMARY = {
    "total_customers": 30000,
    "historical_default_rate_pct": 22.12,
    "historical_defaults": 6636,
    "customers_with_payment_delay": 8000,
    "average_credit_limit": 150000.50,
    "average_latest_utilization_pct": 45.25,
    "customers_with_repeated_delay": 3500,
}

RISK_DATA = [
    {"risk_band": "LOW", "total_customers": 15000},
    {"risk_band": "MEDIUM", "total_customers": 10000},
    {"risk_band": "HIGH", "total_customers": 5000},
]

MONTHLY_DATA = [
    {"activity_month": f"2005-{month:02d}-01"}
    for month in range(4, 10)
]


@pytest.fixture
def ui():
    def columns(spec, **kwargs):
        count = spec if isinstance(spec, int) else len(spec)
        return tuple(nullcontext() for _ in range(count))

    with (
        patch.object(
            overview.st, "columns",
            side_effect=columns,
        ),
        patch.object(
            overview.st, "spinner",
            return_value=nullcontext(),
        ),
        patch.object(
            overview.st, "button",
            return_value=False,
        ) as button,
        patch.object(
            overview.st, "rerun",
        ) as rerun,
        patch.object(
            overview.st, "plotly_chart",
        ) as plot,
        patch.object(
            overview.st, "warning",
        ) as warning,
        patch.object(
            overview.st, "info",
        ) as info,
        patch.object(
            overview.st, "error",
        ) as error,
        patch.object(
            overview, "render_kpi_card",
        ) as kpi,
        patch.object(
            overview, "render_api_error",
        ) as api_error,
        patch.object(
            overview, "load_overview_data",
            return_value=(SUMMARY, RISK_DATA, MONTHLY_DATA),
        ) as load,
        patch.object(
            overview, "create_risk_donut",
            return_value="risk-donut",
        ) as donut,
        patch.object(
            overview, "create_default_rate_chart",
            return_value="default-rate",
        ) as default_chart,
        patch.object(
            overview, "create_monthly_delinquency_chart",
            return_value="monthly-rate",
        ) as monthly_rate,
        patch.object(
            overview, "create_monthly_delay_count_chart",
            return_value="monthly-count",
        ) as monthly_count,
        patch.object(
            overview, "generate_executive_insights",
            return_value=["insight-one"],
        ) as generate,
        patch.object(
            overview, "render_executive_insights",
        ) as render_insights,
    ):
        yield locals()


def test_load_overview_data_fetches_three_apis():
    with (
        patch.object(
            overview,
            "get_portfolio_summary",
            return_value=SUMMARY,
        ) as summary_api,
        patch.object(
            overview,
            "get_risk_distribution",
            return_value=RISK_DATA,
        ) as risk_api,
        patch.object(
            overview,
            "get_monthly_trends",
            return_value=MONTHLY_DATA,
        ) as monthly_api,
    ):
        result = overview.load_overview_data()

    assert result == (SUMMARY, RISK_DATA, MONTHLY_DATA)
    summary_api.assert_called_once_with()
    risk_api.assert_called_once_with()
    monthly_api.assert_called_once_with()


def test_overview_renders_six_kpis(ui):
    overview.render_overview()

    assert ui["kpi"].call_count == 6


def test_overview_formats_kpi_values(ui):
    overview.render_overview()

    values = {
        call.kwargs["label"]: call.kwargs["value"]
        for call in ui["kpi"].call_args_list
    }

    assert values["Total Customers"] == "30,000"
    assert values["Historical Default Rate"] == "22.12%"
    assert values["Customers With Payment Delay"] == "8,000"
    assert values["Average Credit Limit"] == "150,000.50"
    assert values["Average Latest Utilization"] == "45.25%"
    assert values["Repeated Payment Delays"] == "3,500"


def test_overview_renders_four_charts(ui):
    overview.render_overview()

    assert ui["plot"].call_count == 4


def test_overview_passes_risk_data_to_charts(ui):
    overview.render_overview()

    ui["donut"].assert_called_once_with(RISK_DATA)
    ui["default_chart"].assert_called_once_with(RISK_DATA)


def test_overview_passes_monthly_data_to_charts(ui):
    overview.render_overview()

    ui["monthly_rate"].assert_called_once_with(MONTHLY_DATA)
    ui["monthly_count"].assert_called_once_with(MONTHLY_DATA)


def test_overview_renders_executive_insights(ui):
    overview.render_overview()

    ui["generate"].assert_called_once_with(
        SUMMARY, RISK_DATA, MONTHLY_DATA
    )
    ui["render_insights"].assert_called_once_with(
        ["insight-one"]
    )


def test_refresh_button_requests_rerun(ui):
    ui["button"].return_value = True

    overview.render_overview()

    ui["rerun"].assert_called_once_with()


def test_load_failure_stops_rendering(ui):
    ui["load"].side_effect = overview.APIClientError(
        "Backend unavailable"
    )

    overview.render_overview()

    ui["api_error"].assert_called_once()
    ui["kpi"].assert_not_called()
    ui["plot"].assert_not_called()


@pytest.mark.parametrize(
    "bad_data,expected_message",
    [
        (
            {},
            "unexpected format",
        ),
        (
            [],
            "No risk distribution data",
        ),
        (
            [{"risk_band": "LOW"}],
            "incomplete",
        ),
        (
            [
                {"risk_band": "LOW"},
                {"risk_band": "MEDIUM"},
                {"risk_band": "UNKNOWN"},
            ],
            "unexpected risk bands",
        ),
    ],
)
def test_invalid_risk_distribution_stops_charts(
    ui, bad_data, expected_message
):
    ui["load"].return_value = (
        SUMMARY, bad_data, MONTHLY_DATA
    )

    overview.render_overview()

    ui["plot"].assert_not_called()
    ui["generate"].assert_not_called()

    messages = [
        str(call.args[0])
        for mock in (ui["warning"], ui["info"])
        for call in mock.call_args_list
    ]

    assert any(
        expected_message in message
        for message in messages
    )


def test_monthly_chart_value_error_is_displayed(ui):
    ui["monthly_rate"].side_effect = ValueError(
        "Invalid monthly records"
    )

    overview.render_overview()

    ui["error"].assert_called_once()
    assert "Invalid monthly records" in (
        ui["error"].call_args.args[0]
    )


def test_monthly_chart_api_error_is_handled(ui):
    ui["monthly_rate"].side_effect = (
        overview.APIClientError("Monthly service failed")
    )

    overview.render_overview()

    ui["api_error"].assert_called_once()


@pytest.mark.parametrize(
    "exception",
    [
        KeyError("missing"),
        TypeError("invalid"),
        ValueError("bad values"),
        ZeroDivisionError("zero"),
    ],
)
def test_insights_failures_are_handled(ui, exception):
    ui["generate"].side_effect = exception

    overview.render_overview()

    ui["error"].assert_called_once()
    assert "Unable to generate executive insights" in (
        ui["error"].call_args.args[0]
    )


def test_invalid_risk_data_does_not_hide_kpis(ui):
    ui["load"].return_value = (
        SUMMARY, [], MONTHLY_DATA
    )

    overview.render_overview()

    assert ui["kpi"].call_count == 6
    ui["info"].assert_called_once()


def test_overview_risk_charts_render_before_monthly(ui):
    overview.render_overview()

    charts = [
        call.args[0]
        for call in ui["plot"].call_args_list
    ]

    assert charts == [
        "risk-donut",
        "default-rate",
        "monthly-rate",
        "monthly-count",
    ]
