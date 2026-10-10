
import pytest

from src.frontend.api_client import (
    APIClientError,
    get_customers,
    get_customer_detail,
    get_customer_activity,
)


EXPECTED_CUSTOMERS = 30000


def test_customer_count_restored():
    response = get_customers(
        page=1,
        page_size=20,
    )

    assert response["total_records"] == EXPECTED_CUSTOMERS


def test_deleted_customer_not_accessible():
    with pytest.raises(APIClientError) as exc:
        get_customer_detail(30001)

    assert exc.value.status_code == 404


def test_deleted_customer_activity_not_accessible():
    with pytest.raises(APIClientError) as exc:
        get_customer_activity(30001)

    assert exc.value.status_code == 404


@pytest.mark.parametrize("customer_id", [1, 3, 14])
def test_original_customer_integrity(customer_id):
    customer = get_customer_detail(customer_id)
    activity_response = get_customer_activity(customer_id)

    assert customer["customer_id"] == customer_id
    assert activity_response["customer_id"] == customer_id

    profile = customer["credit_profile"]
    risk = customer["risk"]
    activity = activity_response["activity"]

    assert len(activity) == 6

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

    delayed_months = sum(
        row["repayment_status"] > 0
        for row in activity
    )

    assert delayed_months == profile["delay_month_count"]

    component_total = (
        risk["delay_frequency_score"]
        + risk["delay_severity_score"]
        + risk["utilization_score"]
        + risk["payment_behavior_score"]
    )

    assert component_total == risk["risk_score"]

    score = risk["risk_score"]

    expected_band = (
        "LOW" if score <= 2
        else "MEDIUM" if score <= 5
        else "HIGH"
    )

    assert risk["risk_band"] == expected_band


def test_high_risk_filter_still_works():
    response = get_customers(
        page=1,
        page_size=20,
        risk_band="HIGH",
    )

    assert response["items"]

    assert all(
        customer["risk_band"] == "HIGH"
        for customer in response["items"]
    )


def test_pagination_still_works():
    first_page = get_customers(
        page=1,
        page_size=20,
    )

    second_page = get_customers(
        page=2,
        page_size=20,
    )

    first_ids = {
        customer["customer_id"]
        for customer in first_page["items"]
    }

    second_ids = {
        customer["customer_id"]
        for customer in second_page["items"]
    }

    assert len(first_ids) == 20
    assert len(second_ids) == 20
    assert first_ids.isdisjoint(second_ids)


def test_risk_score_sorting():
    response = get_customers(
        page=1,
        page_size=20,
        sort_by="risk_score",
        sort_order="desc",
    )

    scores = [
        customer["risk_score"]
        for customer in response["items"]
    ]

    assert scores == sorted(
        scores,
        reverse=True,
    )
