
import pytest

from src.frontend.components import charts


RISK_DATA = [
    {
        "risk_band": "HIGH",
        "total_customers": 20,
        "historical_defaults": 8,
        "historical_default_rate_pct": 40.0,
    },
    {
        "risk_band": "LOW",
        "total_customers": 60,
        "historical_defaults": 6,
        "historical_default_rate_pct": 10.0,
    },
    {
        "risk_band": "MEDIUM",
        "total_customers": 20,
        "historical_defaults": 6,
        "historical_default_rate_pct": 30.0,
    },
]

MONTHS = [
    "2005-04-01",
    "2005-05-01",
    "2005-06-01",
    "2005-07-01",
    "2005-08-01",
    "2005-09-01",
]


@pytest.fixture
def monthly_data():
    return [
        {
            "activity_month": month,
            "customer_records": 100,
            "delayed_customers": (index + 1) * 10,
            "delayed_customer_rate_pct": (index + 1) * 10.0,
        }
        for index, month in enumerate(MONTHS)
    ]


def test_risk_donut_uses_expected_band_order():
    fig = charts.create_risk_donut(RISK_DATA)

    assert list(fig.data[0].labels) == [
        "LOW", "MEDIUM", "HIGH"
    ]
    assert list(fig.data[0].values) == [60, 20, 20]


def test_risk_donut_total_annotation():
    fig = charts.create_risk_donut(RISK_DATA)

    assert "100" in fig.layout.annotations[0].text


def test_risk_donut_handles_empty_data():
    fig = charts.create_risk_donut([])

    assert len(fig.data[0].labels) == 0


def test_default_rate_chart_values():
    fig = charts.create_default_rate_chart(RISK_DATA)

    assert list(fig.data[0].x) == [
        "LOW", "MEDIUM", "HIGH"
    ]
    assert list(fig.data[0].y) == [
        10.0, 30.0, 40.0
    ]


def test_default_rate_chart_handles_empty_data():
    fig = charts.create_default_rate_chart([])

    assert len(fig.data[0].x) == 0


def test_monthly_validation_sorts_records(monthly_data):
    records = charts.prepare_monthly_trends(
        list(reversed(monthly_data))
    )

    assert [
        row["activity_month"] for row in records
    ] == MONTHS


@pytest.mark.parametrize(
    "invalid",
    [
        None,
        {},
        "invalid",
        123,
    ],
)
def test_monthly_validation_rejects_non_list(invalid):
    with pytest.raises(ValueError):
        charts.prepare_monthly_trends(invalid)


def test_monthly_validation_requires_six_records(monthly_data):
    with pytest.raises(ValueError):
        charts.prepare_monthly_trends(
            monthly_data[:5]
        )


def test_monthly_validation_rejects_wrong_month(monthly_data):
    monthly_data[0]["activity_month"] = "2005-03-01"

    with pytest.raises(ValueError):
        charts.prepare_monthly_trends(monthly_data)


def test_monthly_validation_rejects_zero_customers(monthly_data):
    monthly_data[0]["customer_records"] = 0

    with pytest.raises(ValueError):
        charts.prepare_monthly_trends(monthly_data)


def test_monthly_validation_rejects_negative_delays(monthly_data):
    monthly_data[0]["delayed_customers"] = -1

    with pytest.raises(ValueError):
        charts.prepare_monthly_trends(monthly_data)


def test_monthly_validation_rejects_excess_delays(monthly_data):
    monthly_data[0]["delayed_customers"] = 101

    with pytest.raises(ValueError):
        charts.prepare_monthly_trends(monthly_data)


def test_monthly_validation_rejects_invalid_rate(monthly_data):
    monthly_data[0]["delayed_customer_rate_pct"] = 101.0

    with pytest.raises(ValueError):
        charts.prepare_monthly_trends(monthly_data)


def test_delinquency_chart_values(monthly_data):
    fig = charts.create_monthly_delinquency_chart(
        monthly_data
    )

    assert list(fig.data[0].x) == [
        "Apr", "May", "Jun", "Jul", "Aug", "Sep"
    ]
    assert list(fig.data[0].y) == [
        10.0, 20.0, 30.0, 40.0, 50.0, 60.0
    ]


def test_delayed_customer_chart_values(monthly_data):
    fig = charts.create_monthly_delay_count_chart(
        monthly_data
    )

    assert list(fig.data[0].y) == [
        10, 20, 30, 40, 50, 60
    ]


def test_segment_count_chart():
    data = [
        {"segment": "Male", "total_customers": 60},
        {"segment": "Female", "total_customers": 40},
    ]

    fig = charts.create_segment_count_chart(data)

    assert list(fig.data[0].x) == [60, 40]
    assert list(fig.data[0].y) == ["Male", "Female"]


def test_segment_default_chart():
    data = [
        {
            "segment": "Male",
            "historical_default_rate_pct": 20.0,
            "historical_defaults": 12,
        },
        {
            "segment": "Female",
            "historical_default_rate_pct": 10.0,
            "historical_defaults": 4,
        },
    ]

    fig = charts.create_segment_default_chart(data)

    assert list(fig.data[0].x) == [20.0, 10.0]
    assert list(fig.data[0].y) == ["Male", "Female"]
