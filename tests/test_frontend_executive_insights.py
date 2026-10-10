
from contextlib import nullcontext
from unittest.mock import patch

import pytest

from src.frontend.components import insights


SUMMARY = {
    "total_customers": 100,
    "customers_with_repeated_delay": 25,
}

RISK_DATA = [
    {
        "risk_band": "LOW",
        "historical_default_rate_pct": 10.0,
    },
    {
        "risk_band": "MEDIUM",
        "historical_default_rate_pct": 20.0,
    },
    {
        "risk_band": "HIGH",
        "historical_default_rate_pct": 40.0,
    },
]

MONTHLY_DATA = [
    {
        "activity_month": "2005-04-01",
        "delayed_customer_rate_pct": 15.0,
        "delayed_customers": 15,
    },
    {
        "activity_month": "2005-05-01",
        "delayed_customer_rate_pct": 35.0,
        "delayed_customers": 35,
    },
    {
        "activity_month": "2005-06-01",
        "delayed_customer_rate_pct": 20.0,
        "delayed_customers": 20,
    },
]


def generate(
    summary=None,
    risk_data=None,
    monthly_data=None,
):
    return insights.generate_executive_insights(
        SUMMARY if summary is None else summary,
        RISK_DATA if risk_data is None else risk_data,
        MONTHLY_DATA if monthly_data is None else monthly_data,
    )


@pytest.fixture
def ui():
    def columns(count, **kwargs):
        return tuple(
            nullcontext()
            for _ in range(count)
        )

    with (
        patch.object(
            insights.st,
            "columns",
            side_effect=columns,
        ) as columns_mock,
        patch.object(
            insights.st,
            "markdown",
        ) as markdown,
        patch.object(
            insights.st,
            "info",
        ) as info,
    ):
        yield {
            "columns": columns_mock,
            "markdown": markdown,
            "info": info,
        }


# -------------------------------------
# Insight generation
# -------------------------------------


def test_generates_three_insights():
    result = generate()

    assert len(result) == 3

    assert [item["title"] for item in result] == [
        "Higher Historical Default Rate",
        "Highest Monthly Delinquency",
        "Repeated Payment Delays",
    ]


def test_historical_default_ratio():
    result = generate()

    description = result[0]["description"]

    assert "4.00×" in description
    assert "40.00%" in description
    assert "10.00%" in description


def test_risk_insight_uses_red_tone():
    result = generate()

    assert result[0]["tone"] == "red"


def test_zero_low_risk_rate_skips_ratio():
    risk_data = [
        {
            "risk_band": "LOW",
            "historical_default_rate_pct": 0.0,
        },
        {
            "risk_band": "HIGH",
            "historical_default_rate_pct": 40.0,
        },
    ]

    result = generate(risk_data=risk_data)

    assert all(
        item["title"] != "Higher Historical Default Rate"
        for item in result
    )


def test_missing_high_risk_band_skips_ratio():
    risk_data = [
        {
            "risk_band": "LOW",
            "historical_default_rate_pct": 10.0,
        },
    ]

    result = generate(risk_data=risk_data)

    assert all(
        item["title"] != "Higher Historical Default Rate"
        for item in result
    )


def test_missing_low_risk_band_skips_ratio():
    risk_data = [
        {
            "risk_band": "HIGH",
            "historical_default_rate_pct": 40.0,
        },
    ]

    result = generate(risk_data=risk_data)

    assert all(
        item["title"] != "Higher Historical Default Rate"
        for item in result
    )


def test_empty_risk_distribution_skips_ratio():
    result = generate(risk_data=[])

    assert len(result) == 2


def test_highest_monthly_delinquency_selected():
    result = generate()

    description = result[1]["description"]

    assert "2005-05" in description
    assert "35.00%" in description
    assert "35 customers" in description


def test_monthly_insight_uses_amber_tone():
    result = generate()

    assert result[1]["tone"] == "amber"


def test_empty_monthly_data_skips_peak():
    result = generate(monthly_data=[])

    assert len(result) == 2

    assert all(
        item["title"] != "Highest Monthly Delinquency"
        for item in result
    )


def test_repeated_delay_percentage():
    result = generate()

    description = result[-1]["description"]

    assert "25 customers" in description
    assert "25.00% of the portfolio" in description


def test_repeated_delay_uses_blue_tone():
    result = generate()

    assert result[-1]["tone"] == "blue"


def test_zero_customers_skips_repeated_delay():
    summary = {
        "total_customers": 0,
        "customers_with_repeated_delay": 0,
    }

    result = generate(summary=summary)

    assert len(result) == 2


def test_no_available_insights():
    summary = {
        "total_customers": 0,
        "customers_with_repeated_delay": 0,
    }

    result = generate(
        summary=summary,
        risk_data=[],
        monthly_data=[],
    )

    assert result == []


def test_large_repeated_delay_count_formatted():
    summary = {
        "total_customers": 30000,
        "customers_with_repeated_delay": 12000,
    }

    result = generate(summary=summary)

    description = result[-1]["description"]

    assert "12,000 customers" in description
    assert "40.00%" in description


# -------------------------------------
# Streamlit rendering
# -------------------------------------


def test_empty_insights_displays_info(ui):
    insights.render_executive_insights([])

    ui["info"].assert_called_once_with(
        "Insufficient data to generate "
        "executive insights."
    )

    ui["columns"].assert_not_called()


def test_render_creates_correct_number_of_columns(ui):
    data = generate()

    insights.render_executive_insights(data)

    ui["columns"].assert_called_once_with(
        3,
        gap="medium",
    )


def test_render_creates_heading_and_cards(ui):
    data = generate()

    insights.render_executive_insights(data)

    # One heading plus three insight cards
    assert ui["markdown"].call_count == 4


def test_render_displays_titles(ui):
    data = generate()

    insights.render_executive_insights(data)

    markup = " ".join(
        call.args[0]
        for call in ui["markdown"].call_args_list
    )

    assert "Higher Historical Default Rate" in markup
    assert "Highest Monthly Delinquency" in markup
    assert "Repeated Payment Delays" in markup


def test_render_uses_valid_tone(ui):
    data = [
        {
            "title": "Test Insight",
            "description": "Test Description",
            "tone": "teal",
        }
    ]

    insights.render_executive_insights(data)

    markup = ui["markdown"].call_args_list[-1].args[0]

    assert "cr-insight-teal" in markup


def test_invalid_tone_falls_back_to_blue(ui):
    data = [
        {
            "title": "Test",
            "description": "Description",
            "tone": "purple",
        }
    ]

    insights.render_executive_insights(data)

    markup = ui["markdown"].call_args_list[-1].args[0]

    assert "cr-insight-blue" in markup
    assert "cr-insight-purple" not in markup


def test_missing_tone_defaults_to_blue(ui):
    data = [
        {
            "title": "Test",
            "description": "Description",
        }
    ]

    insights.render_executive_insights(data)

    markup = ui["markdown"].call_args_list[-1].args[0]

    assert "cr-insight-blue" in markup


def test_html_escaping_prevents_markup_injection(ui):
    data = [
        {
            "title": "<script>alert(1)</script>",
            "description": "<b>unsafe</b>",
            "tone": "red",
        }
    ]

    insights.render_executive_insights(data)

    markup = ui["markdown"].call_args_list[-1].args[0]

    assert "&lt;script&gt;" in markup
    assert "&lt;b&gt;unsafe&lt;/b&gt;" in markup

    assert "<script>" not in markup
    assert "<b>unsafe</b>" not in markup


def test_render_uses_unsafe_html_for_styled_cards(ui):
    data = generate()

    insights.render_executive_insights(data)

    for call in ui["markdown"].call_args_list:
        assert call.kwargs["unsafe_allow_html"] is True


def test_single_insight_renders_one_card(ui):
    data = [
        {
            "title": "Single Insight",
            "description": "Only one observation",
            "tone": "blue",
        }
    ]

    insights.render_executive_insights(data)

    ui["columns"].assert_called_once_with(
        1,
        gap="medium",
    )

    assert ui["markdown"].call_count == 2
