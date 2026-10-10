
from contextlib import nullcontext
from unittest.mock import patch

import pytest

from src.frontend.pages import reports_export as reports
from src.frontend.components import risk_segment_reports as segments


RISK_DATA = [
    {
        "risk_band": "HIGH",
        "total_customers": 20,
        "historical_defaults": 8,
        "historical_default_rate_pct": 40.0,
        "average_risk_score": 7.5,
    },
    {
        "risk_band": "LOW",
        "total_customers": 60,
        "historical_defaults": 6,
        "historical_default_rate_pct": 10.0,
        "average_risk_score": 1.2,
    },
    {
        "risk_band": "MEDIUM",
        "total_customers": 20,
        "historical_defaults": 6,
        "historical_default_rate_pct": 30.0,
        "average_risk_score": 4.0,
    },
]

SEGMENT_DATA = [
    {
        "segment": "Male",
        "total_customers": 60,
        "average_credit_limit": 100000.0,
        "historical_defaults": 12,
        "historical_default_rate_pct": 20.0,
        "customers_with_payment_delay": 18,
        "average_latest_utilization_pct": 45.0,
    },
    {
        "segment": "Female",
        "total_customers": 40,
        "average_credit_limit": 120000.0,
        "historical_defaults": 8,
        "historical_default_rate_pct": 20.0,
        "customers_with_payment_delay": 10,
        "average_latest_utilization_pct": 35.0,
    },
]


@pytest.fixture
def ui():
    def columns(sizes, **kwargs):
        count = sizes if isinstance(sizes, int) else len(sizes)
        return tuple(nullcontext() for _ in range(count))

    with (
        patch.object(
            segments.st,
            "columns",
            side_effect=columns,
        ),
        patch.object(
            segments.st,
            "tabs",
            side_effect=lambda labels: [
                nullcontext() for _ in labels
            ],
        ),
        patch.object(
            segments.st,
            "selectbox",
            side_effect=lambda label, options, **kwargs:
                options[0],
        ) as selectbox,
        patch.object(
            segments.st,
            "plotly_chart",
        ) as chart,
        patch.object(
            segments.st,
            "dataframe",
        ) as dataframe,
        patch.object(
            segments.st,
            "download_button",
        ) as download,
        patch.object(
            segments.st,
            "metric",
        ) as metric,
        patch.object(
            segments.st,
            "info",
        ) as info,
        patch.object(
            segments.st,
            "error",
        ) as error,
        patch.object(
            segments,
            "get_risk_distribution",
            return_value=RISK_DATA,
        ) as get_risk,
        patch.object(
            segments,
            "get_segment_analytics",
            return_value=SEGMENT_DATA,
        ) as get_segments,
    ):
        yield {
            "selectbox": selectbox,
            "chart": chart,
            "dataframe": dataframe,
            "download": download,
            "metric": metric,
            "info": info,
            "error": error,
            "get_risk": get_risk,
            "get_segments": get_segments,
        }


def test_risk_distribution_empty_data():
    with (
        patch.object(
            reports.st, "info"
        ) as info,
        patch.object(
            reports.st, "plotly_chart"
        ) as chart,
    ):
        reports.render_risk_distribution([])

    info.assert_called_once_with(
        "No risk distribution data available."
    )
    chart.assert_not_called()


def test_risk_distribution_renders_two_charts():
    with (
        patch.object(
            reports.st, "plotly_chart"
        ) as chart,
        patch.object(
            reports.st, "dataframe"
        ) as dataframe,
    ):
        reports.render_risk_distribution(RISK_DATA)

    assert chart.call_count == 2
    dataframe.assert_called_once()


def test_risk_distribution_sorts_bands():
    with patch.object(
        reports.st, "dataframe"
    ) as dataframe:
        reports.render_risk_distribution(RISK_DATA)

    table = dataframe.call_args.args[0]

    assert list(table["Risk Band"]) == [
        "LOW",
        "MEDIUM",
        "HIGH",
    ]


def test_risk_concentration_calculates_shares(ui):
    segments.render_risk_concentration()

    table = ui["dataframe"].call_args.args[0]

    assert list(table["Risk Band"]) == [
        "LOW",
        "MEDIUM",
        "HIGH",
    ]

    high = table.loc[
        table["Risk Band"] == "HIGH"
    ].iloc[0]

    assert high["Customer Share (%)"] == pytest.approx(20.0)
    assert high["Default Share (%)"] == pytest.approx(40.0)


def test_risk_concentration_csv_download(ui):
    segments.render_risk_concentration()

    kwargs = ui["download"].call_args.kwargs

    assert kwargs["file_name"] == (
        "risk_concentration_report.csv"
    )
    assert kwargs["mime"] == "text/csv"

    content = kwargs["data"].decode("utf-8")

    assert "Customer Share (%)" in content
    assert "Default Share (%)" in content


def test_risk_concentration_empty_response(ui):
    ui["get_risk"].return_value = []

    segments.render_risk_concentration()

    ui["info"].assert_called_once_with(
        "No risk data available."
    )
    ui["download"].assert_not_called()


def test_risk_concentration_api_failure(ui):
    ui["get_risk"].side_effect = segments.APIClientError(
        "Risk API unavailable"
    )

    segments.render_risk_concentration()

    ui["error"].assert_called_once()
    ui["download"].assert_not_called()


@pytest.mark.parametrize(
    "label,expected",
    [
        ("Gender", "gender"),
        ("Education", "education"),
        ("Marital Status", "marital_status"),
        ("Age", "age"),
    ],
)
def test_segment_selection_mapping(ui, label, expected):
    with patch.object(
        segments.st,
        "selectbox",
        return_value=label,
    ):
        segments.render_segment_report()

    ui["get_segments"].assert_called_once_with(expected)


def test_segment_report_totals(ui):
    segments.render_segment_report()

    metric_values = {
        call.args[0]: call.args[1]
        for call in ui["metric"].call_args_list
    }

    assert metric_values["Customers"] == "100"
    assert metric_values["Historical Defaults"] == "20"
    assert metric_values["Customers With Delay"] == "28"


def test_segment_report_renders_charts_and_table(ui):
    segments.render_segment_report()

    assert ui["chart"].call_count == 2
    ui["dataframe"].assert_called_once()


def test_segment_report_csv_download(ui):
    segments.render_segment_report()

    kwargs = ui["download"].call_args.kwargs

    assert kwargs["file_name"] == (
        "gender_segment_report.csv"
    )
    assert kwargs["mime"] == "text/csv"

    content = kwargs["data"].decode("utf-8")

    assert "Segment" in content
    assert "Customers" in content
    assert "Historical Defaults" in content


def test_segment_report_empty_response(ui):
    ui["get_segments"].return_value = []

    segments.render_segment_report()

    ui["info"].assert_called_once_with(
        "No segment data available."
    )
    ui["download"].assert_not_called()


def test_segment_report_api_failure(ui):
    ui["get_segments"].side_effect = (
        segments.APIClientError(
            "Segment API unavailable"
        )
    )

    segments.render_segment_report()

    ui["error"].assert_called_once()
    ui["download"].assert_not_called()


def test_advanced_reports_render_both_sections(ui):
    with (
        patch.object(
            segments,
            "render_risk_concentration",
        ) as risk,
        patch.object(
            segments,
            "render_segment_report",
        ) as segment,
    ):
        segments.render_risk_segment_reports()

    risk.assert_called_once()
    segment.assert_called_once()
