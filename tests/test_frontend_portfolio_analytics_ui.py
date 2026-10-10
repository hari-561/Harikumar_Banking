
from contextlib import nullcontext
from unittest.mock import patch

import pytest

from src.frontend.pages import portfolio_analytics as portfolio


SUMMARY = {
    "total_customers": 100,
    "historical_defaults": 20,
    "total_credit_exposure": 5_000_000_000.0,
    "over_limit_customers": 12,
    "average_credit_limit": 150000.50,
}

SEGMENT_DATA = [
    {
        "segment": "Graduate",
        "total_customers": 60,
        "average_credit_limit": 160000.0,
        "historical_defaults": 12,
        "historical_default_rate_pct": 20.0,
        "customers_with_payment_delay": 18,
        "average_latest_utilization_pct": 45.0,
    },
    {
        "segment": "University",
        "total_customers": 40,
        "average_credit_limit": 135000.0,
        "historical_defaults": 8,
        "historical_default_rate_pct": 20.0,
        "customers_with_payment_delay": 10,
        "average_latest_utilization_pct": 35.0,
    },
]


def copy_segments():
    return [dict(row) for row in SEGMENT_DATA]


@pytest.fixture
def ui():
    def columns(spec, **kwargs):
        count = spec if isinstance(spec, int) else len(spec)
        return tuple(nullcontext() for _ in range(count))

    def selectbox(label, options, **kwargs):
        return options[kwargs.get("index", 0)]

    with (
        patch.object(
            portfolio.st,
            "columns",
            side_effect=columns,
        ),
        patch.object(
            portfolio.st,
            "spinner",
            return_value=nullcontext(),
        ),
        patch.object(
            portfolio.st,
            "selectbox",
            side_effect=selectbox,
        ) as select,
        patch.object(
            portfolio.st,
            "plotly_chart",
        ) as plot,
        patch.object(
            portfolio.st,
            "dataframe",
        ) as dataframe,
        patch.object(
            portfolio.st,
            "warning",
        ) as warning,
        patch.object(
            portfolio.st,
            "error",
        ) as error,
        patch.object(
            portfolio,
            "get_portfolio_summary",
            return_value=SUMMARY,
        ) as summary_api,
        patch.object(
            portfolio,
            "get_customer_segments",
            return_value=copy_segments(),
        ) as segment_api,
        patch.object(
            portfolio,
            "render_kpi_card",
        ) as kpi,
        patch.object(
            portfolio,
            "render_section_header",
        ) as header,
        patch.object(
            portfolio,
            "render_api_error",
        ) as api_error,
        patch.object(
            portfolio,
            "create_segment_count_chart",
            return_value="segment-count-chart",
        ) as count_chart,
        patch.object(
            portfolio,
            "create_segment_default_chart",
            return_value="segment-default-chart",
        ) as default_chart,
        patch.object(
            portfolio,
            "render_segment_drilldown",
        ) as drilldown,
    ):
        yield locals()


# -----------------------------------------
# Segment validation tests
# -----------------------------------------


@pytest.mark.parametrize(
    "invalid",
    [None, {}, "", 123, []],
)
def test_rejects_invalid_segment_container(invalid):
    with pytest.raises(
        ValueError,
        match="no usable records",
    ):
        portfolio.validate_segment_data(invalid)


def test_rejects_non_dictionary_record():
    with pytest.raises(
        ValueError,
        match="Invalid segment record",
    ):
        portfolio.validate_segment_data(["invalid"])


def test_rejects_missing_required_fields():
    data = copy_segments()
    del data[0]["average_credit_limit"]

    with pytest.raises(
        ValueError,
        match="Missing segment fields",
    ):
        portfolio.validate_segment_data(data)


def test_rejects_empty_segment_label():
    data = copy_segments()
    data[0]["segment"] = "   "

    with pytest.raises(
        ValueError,
        match="Empty segment label",
    ):
        portfolio.validate_segment_data(data)


@pytest.mark.parametrize(
    "count",
    [-1, True, 10.5, "100"],
)
def test_rejects_invalid_customer_counts(count):
    data = copy_segments()
    data[0]["total_customers"] = count

    with pytest.raises(
        ValueError,
        match="Invalid customer or default counts",
    ):
        portfolio.validate_segment_data(data)


@pytest.mark.parametrize(
    "defaults",
    [-1, True, 100, 2.5],
)
def test_rejects_invalid_default_counts(defaults):
    data = copy_segments()
    data[0]["historical_defaults"] = defaults

    with pytest.raises(
        ValueError,
        match="Invalid customer or default counts",
    ):
        portfolio.validate_segment_data(data)


@pytest.mark.parametrize(
    "rate",
    [-1, 101],
)
def test_rejects_invalid_default_rates(rate):
    data = copy_segments()
    data[0]["historical_default_rate_pct"] = rate

    with pytest.raises(
        ValueError,
        match="Invalid historical default rate",
    ):
        portfolio.validate_segment_data(data)


def test_rejects_duplicate_segment_labels():
    data = copy_segments()
    data[1]["segment"] = data[0]["segment"]

    with pytest.raises(
        ValueError,
        match="Duplicate segment labels",
    ):
        portfolio.validate_segment_data(data)


def test_valid_segments_are_preserved():
    data = copy_segments()

    result = portfolio.validate_segment_data(data)

    assert result is data
    assert len(result) == 2


# -----------------------------------------
# Portfolio Analytics UI tests
# -----------------------------------------


def test_page_fetches_summary_and_segments(ui):
    portfolio.render_portfolio_analytics()

    ui["summary_api"].assert_called_once_with()
    ui["segment_api"].assert_called_once_with(
        "education"
    )


def test_page_renders_three_portfolio_kpis(ui):
    portfolio.render_portfolio_analytics()

    assert ui["kpi"].call_count == 3


def test_portfolio_kpi_values(ui):
    portfolio.render_portfolio_analytics()

    values = {
        call.args[0]: call.args[1]
        for call in ui["kpi"].call_args_list
    }

    assert values["Total Credit Exposure"] == "5.00B"
    assert values["Over-Limit Customers"] == "12"
    assert values["Average Credit Limit"] == "150,000.50"


@pytest.mark.parametrize(
    "label,expected",
    [
        ("Education", "education"),
        ("Gender", "gender"),
        ("Marital Status", "marital_status"),
        ("Age", "age"),
    ],
)
def test_segment_filter_mapping(ui, label, expected):
    original = ui["select"].side_effect

    def choose_segment(field, options, **kwargs):
        if field == "Segment customers by":
            return label
        return original(field, options, **kwargs)

    ui["select"].side_effect = choose_segment

    portfolio.render_portfolio_analytics()

    ui["segment_api"].assert_called_once_with(expected)


def test_page_renders_two_segment_charts(ui):
    portfolio.render_portfolio_analytics()

    assert ui["plot"].call_count == 2

    assert [
        call.args[0]
        for call in ui["plot"].call_args_list
    ] == [
        "segment-count-chart",
        "segment-default-chart",
    ]


def test_segment_charts_receive_api_data(ui):
    portfolio.render_portfolio_analytics()

    ui["count_chart"].assert_called_once_with(
        SEGMENT_DATA
    )

    ui["default_chart"].assert_called_once_with(
        SEGMENT_DATA
    )


def test_segment_comparison_table(ui):
    portfolio.render_portfolio_analytics()

    rows = ui["dataframe"].call_args.args[0]

    assert len(rows) == 2
    assert rows[0]["Segment"] == "Graduate"
    assert rows[0]["Customers"] == 60
    assert rows[0]["Historical Defaults"] == 12
    assert rows[1]["Segment"] == "University"


def test_drilldown_receives_selected_segment(ui):
    portfolio.render_portfolio_analytics()

    ui["drilldown"].assert_called_once_with(
        SEGMENT_DATA[0],
        SUMMARY,
    )


def test_customer_reconciliation_failure(ui):
    ui["segment_api"].return_value = [
        {
            **SEGMENT_DATA[0],
            "total_customers": 59,
        },
        SEGMENT_DATA[1],
    ]

    portfolio.render_portfolio_analytics()

    ui["warning"].assert_called_once()
    ui["plot"].assert_not_called()
    ui["drilldown"].assert_not_called()


def test_default_reconciliation_failure(ui):
    ui["segment_api"].return_value = [
        {
            **SEGMENT_DATA[0],
            "historical_defaults": 11,
        },
        SEGMENT_DATA[1],
    ]

    portfolio.render_portfolio_analytics()

    ui["warning"].assert_called_once()
    ui["plot"].assert_not_called()
    ui["drilldown"].assert_not_called()


def test_summary_api_failure_stops_page(ui):
    ui["summary_api"].side_effect = (
        portfolio.APIClientError(
            "Summary service unavailable"
        )
    )

    portfolio.render_portfolio_analytics()

    ui["api_error"].assert_called_once()
    ui["segment_api"].assert_not_called()
    ui["kpi"].assert_not_called()


def test_segment_api_failure_is_handled(ui):
    ui["segment_api"].side_effect = (
        portfolio.APIClientError(
            "Segment service unavailable"
        )
    )

    portfolio.render_portfolio_analytics()

    ui["api_error"].assert_called_once()
    ui["plot"].assert_not_called()


def test_invalid_segment_data_displays_error(ui):
    ui["segment_api"].return_value = []

    portfolio.render_portfolio_analytics()

    ui["error"].assert_called_once()
    assert "Unable to display segment analytics" in (
        ui["error"].call_args.args[0]
    )


def test_page_renders_expected_sections(ui):
    portfolio.render_portfolio_analytics()

    titles = [
        call.args[0]
        for call in ui["header"].call_args_list
    ]

    assert titles == [
        "Portfolio Exposure",
        "Customer Segment Analysis",
        "Segment Comparison",
        "Segment Drill-Down",
    ]


def test_drilldown_selection_uses_correct_record(ui):
    def choose_second(label, options, **kwargs):
        if label == "Select a segment to analyze":
            return "University"
        return options[kwargs.get("index", 0)]

    ui["select"].side_effect = choose_second

    portfolio.render_portfolio_analytics()

    ui["drilldown"].assert_called_once_with(
        SEGMENT_DATA[1],
        SUMMARY,
    )
