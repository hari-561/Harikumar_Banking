
from contextlib import nullcontext
from unittest.mock import patch

import pytest

from src.frontend.pages import risk_analysis as risk


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


@pytest.fixture
def ui():
    def columns(spec, **kwargs):
        count = spec if isinstance(spec, int) else len(spec)
        return tuple(nullcontext() for _ in range(count))

    with (
        patch.object(
            risk.st, "spinner",
            return_value=nullcontext(),
        ),
        patch.object(
            risk.st, "columns",
            side_effect=columns,
        ),
        patch.object(
            risk.st, "expander",
            return_value=nullcontext(),
        ) as expander,
        patch.object(
            risk.st, "plotly_chart",
        ) as plot,
        patch.object(
            risk.st, "dataframe",
        ) as dataframe,
        patch.object(
            risk.st, "markdown",
        ) as markdown,
        patch.object(
            risk.st, "caption",
        ) as caption,
        patch.object(
            risk.st, "error",
        ) as error,
        patch.object(
            risk, "get_risk_distribution",
            return_value=RISK_DATA,
        ) as api,
        patch.object(
            risk, "render_kpi_card",
        ) as kpi,
        patch.object(
            risk, "render_section_header",
        ) as header,
        patch.object(
            risk, "render_api_error",
        ) as api_error,
        patch.object(
            risk, "create_risk_donut",
            return_value="risk-donut",
        ) as donut,
        patch.object(
            risk, "create_default_rate_chart",
            return_value="default-rate",
        ) as default_chart,
    ):
        yield {
            "api": api,
            "kpi": kpi,
            "header": header,
            "api_error": api_error,
            "error": error,
            "plot": plot,
            "dataframe": dataframe,
            "markdown": markdown,
            "caption": caption,
            "expander": expander,
            "donut": donut,
            "default_chart": default_chart,
        }


def test_risk_page_fetches_distribution(ui):
    risk.render_risk_analysis()

    ui["api"].assert_called_once_with()


def test_risk_page_renders_three_kpis(ui):
    risk.render_risk_analysis()

    assert ui["kpi"].call_count == 3


def test_high_risk_customer_share(ui):
    risk.render_risk_analysis()

    call = ui["kpi"].call_args_list[0]

    assert call.args[0] == "HIGH-Risk Customers"
    assert call.args[1] == "20"
    assert call.args[2] == "20.00% of the portfolio"


def test_high_risk_default_rate_kpi(ui):
    risk.render_risk_analysis()

    call = ui["kpi"].call_args_list[1]

    assert call.args[0] == (
        "HIGH-Risk Historical Default Rate"
    )
    assert call.args[1] == "40.00%"
    assert "8 observed defaults" in call.args[2]


def test_high_risk_score_kpi(ui):
    risk.render_risk_analysis()

    call = ui["kpi"].call_args_list[2]

    assert call.args[0] == "Average HIGH Risk Score"
    assert call.args[1] == "7.50"


def test_risk_page_renders_two_charts(ui):
    risk.render_risk_analysis()

    assert ui["plot"].call_count == 2

    assert [
        call.args[0]
        for call in ui["plot"].call_args_list
    ] == ["risk-donut", "default-rate"]


def test_risk_page_passes_distribution_to_charts(ui):
    risk.render_risk_analysis()

    ui["donut"].assert_called_once_with(RISK_DATA)
    ui["default_chart"].assert_called_once_with(
        RISK_DATA
    )


def test_comparison_table_has_correct_band_order(ui):
    risk.render_risk_analysis()

    rows = ui["dataframe"].call_args_list[0].args[0]

    assert [
        row["Risk Band"] for row in rows
    ] == ["LOW", "MEDIUM", "HIGH"]


def test_comparison_table_calculates_shares(ui):
    risk.render_risk_analysis()

    rows = ui["dataframe"].call_args_list[0].args[0]

    shares = {
        row["Risk Band"]: row["Portfolio Share (%)"]
        for row in rows
    }

    assert shares == {
        "LOW": 60.0,
        "MEDIUM": 20.0,
        "HIGH": 20.0,
    }


def test_scoring_methodology_is_rendered(ui):
    risk.render_risk_analysis()

    ui["expander"].assert_called_once_with(
        "View scoring components and thresholds",
        expanded=True,
    )

    text = " ".join(
        str(call.args[0])
        for call in ui["markdown"].call_args_list
    )

    assert "Repayment Delay Frequency" in text
    assert "Maximum Repayment Delay" in text
    assert "Latest Credit Utilization" in text
    assert "Payment-to-Bill Ratio" in text


def test_scoring_classification_ranges(ui):
    risk.render_risk_analysis()

    rows = ui["dataframe"].call_args_list[1].args[0]

    assert rows == [
        {"Risk Band": "LOW", "Score Range": "0–2"},
        {"Risk Band": "MEDIUM", "Score Range": "3–5"},
        {"Risk Band": "HIGH", "Score Range": "6–11"},
    ]


def test_api_failure_stops_page(ui):
    ui["api"].side_effect = risk.APIClientError(
        "Risk API unavailable"
    )

    risk.render_risk_analysis()

    ui["api_error"].assert_called_once()
    ui["kpi"].assert_not_called()
    ui["plot"].assert_not_called()


@pytest.mark.parametrize(
    "bad_data",
    [
        None,
        {},
        "invalid",
        [],
        [{"risk_band": "LOW", "total_customers": 10}],
        [
            {"risk_band": "LOW", "total_customers": 10},
            {"risk_band": "MEDIUM", "total_customers": 20},
            {"risk_band": "UNKNOWN", "total_customers": 30},
        ],
    ],
)
def test_invalid_distribution_is_rejected(ui, bad_data):
    ui["api"].return_value = bad_data

    risk.render_risk_analysis()

    ui["error"].assert_called_once()
    assert "Invalid risk distribution data" in (
        ui["error"].call_args.args[0]
    )

    ui["kpi"].assert_not_called()
    ui["plot"].assert_not_called()


def test_zero_total_customers_is_rejected(ui):
    data = [
        {**row, "total_customers": 0}
        for row in RISK_DATA
    ]

    ui["api"].return_value = data

    risk.render_risk_analysis()

    ui["error"].assert_called_once()
    ui["kpi"].assert_not_called()


def test_missing_customer_count_is_rejected(ui):
    data = [
        dict(row)
        for row in RISK_DATA
    ]

    del data[0]["total_customers"]

    ui["api"].return_value = data

    risk.render_risk_analysis()

    ui["error"].assert_called_once()
    ui["plot"].assert_not_called()


def test_duplicate_risk_band_is_rejected(ui):
    data = [
        dict(row)
        for row in RISK_DATA
    ]

    data[1]["risk_band"] = "HIGH"

    ui["api"].return_value = data

    risk.render_risk_analysis()

    ui["error"].assert_called_once()
    ui["kpi"].assert_not_called()


def test_risk_page_renders_four_section_headers(ui):
    risk.render_risk_analysis()

    titles = [
        call.args[0]
        for call in ui["header"].call_args_list
    ]

    assert titles == [
        "Risk Classification Overview",
        "Risk Distribution",
        "Risk Band Comparison",
        "Risk Scoring Methodology",
    ]


def test_risk_page_displays_historical_disclaimer(ui):
    risk.render_risk_analysis()

    captions = " ".join(
        call.args[0]
        for call in ui["caption"].call_args_list
    )

    assert "not machine learning" in captions
    assert "individual default probabilities" in captions
