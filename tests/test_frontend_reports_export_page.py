
from contextlib import nullcontext
from unittest.mock import patch

import pytest

from src.frontend.pages import reports_export as reports


SUMMARY = {
    "total_customers": 30000,
    "total_credit_exposure": 500000000.0,
    "average_credit_limit": 16666.67,
    "historical_defaults": 6636,
    "historical_default_rate_pct": 22.12,
    "average_latest_utilization_pct": 45.5,
    "customers_with_payment_delay": 8000,
    "customers_with_repeated_delay": 3500,
    "over_limit_customers": 1200,
    "total_bill_amount_6m": 150000000.0,
    "total_payment_amount_6m": 90000000.0,
}

RISK_DATA = [
    {
        "risk_band": "LOW",
        "total_customers": 15000,
        "historical_defaults": 1000,
        "historical_default_rate_pct": 6.67,
        "average_risk_score": 1.5,
    },
    {
        "risk_band": "MEDIUM",
        "total_customers": 10000,
        "historical_defaults": 3000,
        "historical_default_rate_pct": 30.0,
        "average_risk_score": 4.0,
    },
    {
        "risk_band": "HIGH",
        "total_customers": 5000,
        "historical_defaults": 2636,
        "historical_default_rate_pct": 52.72,
        "average_risk_score": 7.0,
    },
]


@pytest.fixture
def page():
    with (
        patch.object(
            reports, "render_section_header"
        ) as header,
        patch.object(
            reports, "get_portfolio_summary",
            return_value=SUMMARY,
        ) as summary_api,
        patch.object(
            reports, "get_risk_distribution",
            return_value=RISK_DATA,
        ) as risk_api,
        patch.object(
            reports, "render_portfolio_metrics"
        ) as metrics,
        patch.object(
            reports, "render_risk_distribution"
        ) as distribution,
        patch.object(
            reports, "render_customer_export"
        ) as customer_export,
        patch.object(
            reports, "render_risk_segment_reports"
        ) as advanced,
        patch.object(
            reports, "render_api_error"
        ) as api_error,
    ):
        yield {
            "header": header,
            "summary_api": summary_api,
            "risk_api": risk_api,
            "metrics": metrics,
            "distribution": distribution,
            "customer_export": customer_export,
            "advanced": advanced,
            "api_error": api_error,
        }


def test_page_fetches_portfolio_and_risk_data(page):
    reports.render_reports_export()

    page["summary_api"].assert_called_once_with()
    page["risk_api"].assert_called_once_with()


def test_page_passes_summary_to_metrics(page):
    reports.render_reports_export()

    page["metrics"].assert_called_once_with(SUMMARY)


def test_page_passes_risk_data_to_distribution(page):
    reports.render_reports_export()

    page["distribution"].assert_called_once_with(
        RISK_DATA
    )


def test_page_renders_customer_export(page):
    reports.render_reports_export()

    page["customer_export"].assert_called_once_with()


def test_page_renders_advanced_reports(page):
    reports.render_reports_export()

    page["advanced"].assert_called_once_with()


def test_page_renders_sections_in_expected_order(page):
    calls = []

    page["metrics"].side_effect = (
        lambda *args: calls.append("metrics")
    )
    page["distribution"].side_effect = (
        lambda *args: calls.append("risk")
    )
    page["customer_export"].side_effect = (
        lambda *args: calls.append("export")
    )
    page["advanced"].side_effect = (
        lambda *args: calls.append("advanced")
    )

    reports.render_reports_export()

    assert calls == [
        "metrics",
        "risk",
        "export",
        "advanced",
    ]


def test_summary_api_failure_blocks_page(page):
    page["summary_api"].side_effect = (
        reports.APIClientError(
            "Portfolio service unavailable"
        )
    )

    reports.render_reports_export()

    page["api_error"].assert_called_once()
    page["risk_api"].assert_not_called()
    page["metrics"].assert_not_called()
    page["distribution"].assert_not_called()
    page["customer_export"].assert_not_called()
    page["advanced"].assert_not_called()


def test_risk_api_failure_blocks_page(page):
    page["risk_api"].side_effect = (
        reports.APIClientError(
            "Risk service unavailable"
        )
    )

    reports.render_reports_export()

    page["summary_api"].assert_called_once()
    page["api_error"].assert_called_once()
    page["metrics"].assert_not_called()
    page["distribution"].assert_not_called()
    page["customer_export"].assert_not_called()
    page["advanced"].assert_not_called()


def test_empty_risk_data_is_forwarded(page):
    page["risk_api"].return_value = []

    reports.render_reports_export()

    page["distribution"].assert_called_once_with([])
    page["customer_export"].assert_called_once()
    page["advanced"].assert_called_once()


def test_empty_portfolio_summary_is_forwarded(page):
    page["summary_api"].return_value = {}

    reports.render_reports_export()

    page["metrics"].assert_called_once_with({})


def test_portfolio_metrics_format_values():
    def columns(sizes, **kwargs):
        count = (
            sizes
            if isinstance(sizes, int)
            else len(sizes)
        )
        return tuple(
            nullcontext()
            for _ in range(count)
        )

    with (
        patch.object(
            reports.st, "columns",
            side_effect=columns,
        ),
        patch.object(
            reports.st, "metric"
        ) as metric,
    ):
        reports.render_portfolio_metrics(SUMMARY)

    values = {
        call.args[0]: call.args[1]
        for call in metric.call_args_list
    }

    assert values["Total Customers"] == "30,000"
    assert values["Total Credit Exposure"] == (
        "500,000,000.00"
    )
    assert values["Historical Defaults"] == "6,636"
    assert values["Historical Default Rate"] == "22.12%"
    assert values["Average Latest Utilization"] == "45.50%"
    assert values["Customers With Payment Delay"] == "8,000"
    assert values["Repeated Payment Delays"] == "3,500"
    assert values["Over-Limit Customers"] == "1,200"
    assert values["Total Bills (6 Months)"] == (
        "150,000,000.00"
    )
    assert values["Total Payments (6 Months)"] == (
        "90,000,000.00"
    )


def test_portfolio_metrics_display_all_11_metrics():
    def columns(sizes, **kwargs):
        count = (
            sizes
            if isinstance(sizes, int)
            else len(sizes)
        )
        return tuple(
            nullcontext()
            for _ in range(count)
        )

    with (
        patch.object(
            reports.st, "columns",
            side_effect=columns,
        ),
        patch.object(
            reports.st, "metric"
        ) as metric,
    ):
        reports.render_portfolio_metrics(SUMMARY)

    assert metric.call_count == 11
