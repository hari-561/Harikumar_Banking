
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from src.api.main import app
from src.api.security.dependencies import get_current_user


SUMMARY = {
    "total_customers": 30000,
    "total_credit_exposure": 500000000.0,
    "average_credit_limit": 16666.67,
    "historical_defaults": 6636,
    "historical_default_rate_pct": 22.12,
    "customers_with_payment_delay": 10000,
    "customers_with_repeated_delay": 5000,
    "average_latest_utilization_pct": 40.0,
    "over_limit_customers": 100,
    "total_bill_amount_6m": 90000000.0,
    "total_payment_amount_6m": 40000000.0,
}

RISK_DISTRIBUTION = [{
    "risk_band": "HIGH",
    "total_customers": 100,
    "historical_defaults": 30,
    "historical_default_rate_pct": 30.0,
    "average_risk_score": 7.5,
}]

MONTHLY_TRENDS = [{
    "activity_month": "2026-09-01",
    "customer_records": 100,
    "total_bill_amount": 500000.0,
    "average_bill_amount": 5000.0,
    "total_payment_amount": 200000.0,
    "average_payment_amount": 2000.0,
    "delayed_customers": 20,
    "delayed_customer_rate_pct": 20.0,
}]

SEGMENTS = [{
    "segment": "Male",
    "total_customers": 100,
    "average_credit_limit": 50000.0,
    "historical_defaults": 20,
    "historical_default_rate_pct": 20.0,
    "customers_with_payment_delay": 30,
    "average_latest_utilization_pct": 40.0,
}]


class TestAnalyticsAPIValidation(unittest.TestCase):

    def setUp(self):
        app.dependency_overrides.clear()
        self.client = TestClient(app)
        self.set_role("ADMIN")

    def tearDown(self):
        app.dependency_overrides.clear()

    def set_role(self, role):
        app.dependency_overrides[get_current_user] = lambda: {
            "user_id": 1,
            "username": "testuser",
            "email": "test@example.com",
            "role": role,
        }

    def test_summary_response(self):
        with patch(
            "src.api.routes.analytics.get_portfolio_summary",
            return_value=SUMMARY
        ):
            response = self.client.get("/analytics/summary")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json()["total_customers"], 30000
        )
        self.assertEqual(
            set(response.json()), set(SUMMARY)
        )

    def test_summary_response_schema_failure(self):
        with patch(
            "src.api.routes.analytics.get_portfolio_summary",
            return_value={"total_customers": 30000}
        ):
            with self.assertRaises(Exception):
                self.client.get("/analytics/summary")

    def test_risk_distribution_response(self):
        with patch(
            "src.api.routes.analytics.get_risk_distribution",
            return_value=RISK_DISTRIBUTION
        ):
            response = self.client.get(
                "/analytics/risk-distribution"
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json()[0]["risk_band"], "HIGH"
        )
        self.assertEqual(
            response.json()[0]["average_risk_score"], 7.5
        )

    def test_risk_distribution_empty(self):
        with patch(
            "src.api.routes.analytics.get_risk_distribution",
            return_value=[]
        ):
            response = self.client.get(
                "/analytics/risk-distribution"
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), [])

    def test_monthly_trends_response(self):
        with patch(
            "src.api.routes.analytics.get_monthly_trends",
            return_value=MONTHLY_TRENDS
        ):
            response = self.client.get(
                "/analytics/monthly-trends"
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json()[0]["activity_month"],
            "2026-09-01"
        )
        self.assertEqual(
            response.json()[0]["delayed_customers"], 20
        )

    def test_monthly_trends_empty(self):
        with patch(
            "src.api.routes.analytics.get_monthly_trends",
            return_value=[]
        ):
            response = self.client.get(
                "/analytics/monthly-trends"
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), [])

    def test_segments_gender(self):
        with patch(
            "src.api.routes.analytics.get_segment_analytics",
            return_value=SEGMENTS
        ) as mock_service:
            response = self.client.get(
                "/analytics/segments?segment=gender"
            )

        self.assertEqual(response.status_code, 200)
        mock_service.assert_called_once_with("gender")
        self.assertEqual(
            response.json()[0]["total_customers"], 100
        )

    def test_all_valid_segment_values(self):
        for segment in [
            "gender",
            "education",
            "marital_status",
            "age",
        ]:
            with self.subTest(segment=segment):
                with patch(
                    "src.api.routes.analytics.get_segment_analytics",
                    return_value=[]
                ) as mock_service:
                    response = self.client.get(
                        "/analytics/segments",
                        params={"segment": segment}
                    )

                self.assertEqual(response.status_code, 200)
                mock_service.assert_called_once_with(segment)

    def test_missing_segment_rejected(self):
        response = self.client.get("/analytics/segments")
        self.assertEqual(response.status_code, 422)

    def test_invalid_segment_rejected(self):
        with patch(
            "src.api.routes.analytics.get_segment_analytics"
        ) as mock_service:
            response = self.client.get(
                "/analytics/segments?segment=income"
            )

        self.assertEqual(response.status_code, 422)
        mock_service.assert_not_called()

    def test_unauthenticated_summary_rejected(self):
        app.dependency_overrides.clear()

        response = self.client.get("/analytics/summary")

        self.assertEqual(response.status_code, 401)

    def test_invalid_token_rejected(self):
        app.dependency_overrides.clear()

        response = self.client.get(
            "/analytics/monthly-trends",
            headers={
                "Authorization": "Bearer invalid.jwt.token"
            }
        )

        self.assertEqual(response.status_code, 401)

    def test_viewer_can_access_summary(self):
        self.set_role("VIEWER")

        with patch(
            "src.api.routes.analytics.get_portfolio_summary",
            return_value=SUMMARY
        ):
            response = self.client.get("/analytics/summary")

        self.assertEqual(response.status_code, 200)

    def test_analyst_can_access_segments(self):
        self.set_role("ANALYST")

        with patch(
            "src.api.routes.analytics.get_segment_analytics",
            return_value=[]
        ):
            response = self.client.get(
                "/analytics/segments?segment=age"
            )

        self.assertEqual(response.status_code, 200)


if __name__ == "__main__":
    unittest.main()
