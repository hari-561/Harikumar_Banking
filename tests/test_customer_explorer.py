
import pytest

from src.frontend.api_client import (
    get_customers,
    get_customer_detail,
    get_customer_activity,
)


@pytest.mark.parametrize(
    "customer_id",
    [1, 3, 14],
)
def test_customer_profile_and_activity(customer_id):

    customer = get_customer_detail(customer_id)
    activity_response = get_customer_activity(customer_id)

    profile = customer["credit_profile"]
    risk = customer["risk"]
    activity = activity_response["activity"]

    assert customer["customer_id"] == customer_id
    assert activity_response["customer_id"] == customer_id

    assert len(activity) == 6

    # Check monthly records are unique and chronological.
    months = [row["activity_month"] for row in activity]

    assert months == sorted(months)
    assert len(set(months)) == 6

    # Reconcile billing and payments.
    total_bills = sum(
        row["bill_amount"] for row in activity
    )

    total_payments = sum(
        row["payment_amount"] for row in activity
    )

    assert total_bills == pytest.approx(
        profile["total_bill_amount_6m"],
        abs=0.01,
    )

    assert total_payments == pytest.approx(
        profile["total_payment_amount_6m"],
        abs=0.01,
    )

    # Reconcile delayed months.
    delayed_months = sum(
        row["repayment_status"] > 0
        for row in activity
    )

    assert delayed_months == profile["delay_month_count"]

    # Reconcile risk components.
    calculated_score = (
        risk["delay_frequency_score"]
        + risk["delay_severity_score"]
        + risk["utilization_score"]
        + risk["payment_behavior_score"]
    )

    assert calculated_score == risk["risk_score"]

    # Verify risk band.
    score = risk["risk_score"]

    expected_band = (
        "LOW" if score <= 2
        else "MEDIUM" if score <= 5
        else "HIGH"
    )

    assert risk["risk_band"] == expected_band


def test_customer_listing_pagination():

    response = get_customers(
        page=1,
        page_size=20,
    )

    assert response["page"] == 1
    assert response["page_size"] == 20
    assert len(response["items"]) <= 20

    assert response["total_records"] >= len(
        response["items"]
    )


def test_high_risk_filter():

    response = get_customers(
        page=1,
        page_size=20,
        risk_band="HIGH",
    )

    assert all(
        row["risk_band"] == "HIGH"
        for row in response["items"]
    )


def test_customer_sorting():

    response = get_customers(
        page=1,
        page_size=20,
        sort_by="risk_score",
        sort_order="desc",
    )

    scores = [
        row["risk_score"]
        for row in response["items"]
    ]

    assert scores == sorted(
        scores,
        reverse=True,
    )
