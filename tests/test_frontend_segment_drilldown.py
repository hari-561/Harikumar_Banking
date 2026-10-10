
from contextlib import nullcontext
from unittest.mock import patch

import pytest

from src.frontend.components import segment_drilldown as drilldown


SEGMENT = {
    "segment": "Graduate",
    "total_customers": 40,
    "historical_default_rate_pct": 30.0,
    "average_credit_limit": 200000.0,
    "average_latest_utilization_pct": 60.0,
    "customers_with_payment_delay": 16,
}

SUMMARY = {
    "total_customers": 100,
    "historical_default_rate_pct": 20.0,
    "average_credit_limit": 150000.0,
    "average_latest_utilization_pct": 45.0,
    "customers_with_payment_delay": 25,
}


@pytest.fixture
def comparison():
    return drilldown.calculate_segment_comparison(
        SEGMENT, SUMMARY
    )


@pytest.fixture
def ui():
    def columns(count, **kwargs):
        return tuple(nullcontext() for _ in range(count))

    with (
        patch.object(
            drilldown.st, "columns",
            side_effect=columns,
        ) as columns_mock,
        patch.object(
            drilldown.st, "metric",
        ) as metric,
        patch.object(
            drilldown.st, "caption",
        ) as caption,
        patch.object(
            drilldown.st, "markdown",
        ) as markdown,
        patch.object(
            drilldown.st, "plotly_chart",
        ) as plot,
    ):
        yield {
            "columns": columns_mock,
            "metric": metric,
            "caption": caption,
            "markdown": markdown,
            "plot": plot,
        }


# ----------------------------------------
# Segment comparison calculations
# ----------------------------------------


def test_comparison_contains_four_metrics(comparison):
    assert set(comparison) == {
        "default_rate",
        "credit_limit",
        "utilization",
        "payment_delay",
    }


def test_default_rate_comparison(comparison):
    assert comparison["default_rate"] == {
        "value": 30.0,
        "baseline": 20.0,
        "difference": 10.0,
    }


def test_credit_limit_comparison(comparison):
    assert comparison["credit_limit"] == {
        "value": 200000.0,
        "baseline": 150000.0,
        "difference": 50000.0,
    }


def test_utilization_comparison(comparison):
    assert comparison["utilization"] == {
        "value": 60.0,
        "baseline": 45.0,
        "difference": 15.0,
    }


def test_payment_delay_comparison(comparison):
    assert comparison["payment_delay"] == {
        "count": 16,
        "value": 40.0,
        "baseline": 25.0,
        "difference": 15.0,
    }


def test_segment_customer_count_must_be_positive():
    segment = {
        **SEGMENT,
        "total_customers": 0,
    }

    with pytest.raises(
        ValueError,
        match="Customer counts must be positive",
    ):
        drilldown.calculate_segment_comparison(
            segment, SUMMARY
        )


def test_portfolio_customer_count_must_be_positive():
    summary = {
        **SUMMARY,
        "total_customers": 0,
    }

    with pytest.raises(
        ValueError,
        match="Customer counts must be positive",
    ):
        drilldown.calculate_segment_comparison(
            SEGMENT, summary
        )


def test_negative_customer_count_is_rejected():
    segment = {
        **SEGMENT,
        "total_customers": -10,
    }

    with pytest.raises(ValueError):
        drilldown.calculate_segment_comparison(
            segment, SUMMARY
        )


def test_zero_payment_delays():
    segment = {
        **SEGMENT,
        "customers_with_payment_delay": 0,
    }

    result = drilldown.calculate_segment_comparison(
        segment, SUMMARY
    )

    assert result["payment_delay"]["value"] == 0.0
    assert result["payment_delay"]["difference"] == -25.0


def test_equal_segment_and_portfolio_metrics():
    segment = {
        **SEGMENT,
        "historical_default_rate_pct": 20.0,
        "average_credit_limit": 150000.0,
        "average_latest_utilization_pct": 45.0,
        "customers_with_payment_delay": 10,
    }

    result = drilldown.calculate_segment_comparison(
        segment, SUMMARY
    )

    assert result["default_rate"]["difference"] == 0
    assert result["credit_limit"]["difference"] == 0
    assert result["utilization"]["difference"] == 0
    assert result["payment_delay"]["difference"] == 0


# ----------------------------------------
# Streamlit rendering
# ----------------------------------------


def test_render_displays_selected_segment(ui):
    with patch.object(
        drilldown, "render_comparison_chart"
    ):
        drilldown.render_segment_drilldown(
            SEGMENT, SUMMARY
        )

    markup = [
        call.args[0]
        for call in ui["markdown"].call_args_list
    ]

    assert "### Selected Segment: Graduate" in markup


def test_render_displays_four_metrics(ui):
    with patch.object(
        drilldown, "render_comparison_chart"
    ):
        drilldown.render_segment_drilldown(
            SEGMENT, SUMMARY
        )

    assert ui["metric"].call_count == 4


def test_render_default_rate_metric(ui):
    with patch.object(
        drilldown, "render_comparison_chart"
    ):
        drilldown.render_segment_drilldown(
            SEGMENT, SUMMARY
        )

    call = ui["metric"].call_args_list[0]

    assert call.args[:3] == (
        "Historical Default Rate",
        "30.00%",
        "+10.00 pp",
    )

    assert call.kwargs["delta_color"] == "inverse"


def test_render_credit_limit_metric(ui):
    with patch.object(
        drilldown, "render_comparison_chart"
    ):
        drilldown.render_segment_drilldown(
            SEGMENT, SUMMARY
        )

    call = ui["metric"].call_args_list[1]

    assert call.args[:3] == (
        "Average Credit Limit",
        "200,000.00",
        "+50,000.00",
    )


def test_render_utilization_metric(ui):
    with patch.object(
        drilldown, "render_comparison_chart"
    ):
        drilldown.render_segment_drilldown(
            SEGMENT, SUMMARY
        )

    call = ui["metric"].call_args_list[2]

    assert call.args[:3] == (
        "Average Latest Utilization",
        "60.00%",
        "+15.00 pp",
    )


def test_render_payment_delay_metric(ui):
    with patch.object(
        drilldown, "render_comparison_chart"
    ):
        drilldown.render_segment_drilldown(
            SEGMENT, SUMMARY
        )

    call = ui["metric"].call_args_list[3]

    assert call.args[:3] == (
        "Customers With Payment Delay",
        "16",
        "40.00% of segment",
    )


def test_render_displays_portfolio_baselines(ui):
    with patch.object(
        drilldown, "render_comparison_chart"
    ):
        drilldown.render_segment_drilldown(
            SEGMENT, SUMMARY
        )

    captions = " ".join(
        call.args[0]
        for call in ui["caption"].call_args_list
    )

    assert "Portfolio baseline: 20.00%" in captions
    assert "Portfolio baseline: 150,000.00" in captions
    assert "Portfolio baseline: 45.00%" in captions
    assert "Portfolio delay rate: 25.00%" in captions


def test_render_passes_comparison_to_chart(ui, comparison):
    with patch.object(
        drilldown, "render_comparison_chart"
    ) as chart:
        drilldown.render_segment_drilldown(
            SEGMENT, SUMMARY
        )

    chart.assert_called_once_with(comparison)


# ----------------------------------------
# Plotly comparison chart
# ----------------------------------------


def test_chart_contains_two_bar_traces(ui, comparison):
    drilldown.render_comparison_chart(comparison)

    fig = ui["plot"].call_args.args[0]

    assert len(fig.data) == 2
    assert fig.data[0].type == "bar"
    assert fig.data[1].type == "bar"


def test_chart_trace_names(ui, comparison):
    drilldown.render_comparison_chart(comparison)

    fig = ui["plot"].call_args.args[0]

    assert fig.data[0].name == "Selected Segment"
    assert fig.data[1].name == "Overall Portfolio"


def test_chart_segment_values(ui, comparison):
    drilldown.render_comparison_chart(comparison)

    fig = ui["plot"].call_args.args[0]

    assert list(fig.data[0].y) == [
        30.0,
        60.0,
        40.0,
    ]


def test_chart_portfolio_values(ui, comparison):
    drilldown.render_comparison_chart(comparison)

    fig = ui["plot"].call_args.args[0]

    assert list(fig.data[1].y) == [
        20.0,
        45.0,
        25.0,
    ]


def test_chart_uses_grouped_bars(ui, comparison):
    drilldown.render_comparison_chart(comparison)

    fig = ui["plot"].call_args.args[0]

    assert fig.layout.barmode == "group"
    assert fig.layout.yaxis.title.text == "Percentage (%)"


def test_chart_has_three_categories(ui, comparison):
    drilldown.render_comparison_chart(comparison)

    fig = ui["plot"].call_args.args[0]

    assert list(fig.data[0].x) == [
        "Historical Default Rate",
        "Average Utilization",
        "Payment Delay Rate",
    ]


def test_chart_disables_plotly_modebar(ui, comparison):
    drilldown.render_comparison_chart(comparison)

    assert ui["plot"].call_args.kwargs["config"] == {
        "displayModeBar": False
    }

