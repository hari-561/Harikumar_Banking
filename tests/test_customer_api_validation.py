
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from src.api.main import app
from src.api.security.dependencies import get_current_user


class TestCustomerAPIValidation(unittest.TestCase):

    def setUp(self):
        app.dependency_overrides.clear()
        app.dependency_overrides[get_current_user] = lambda: {
            "user_id": 1,
            "username": "testadmin",
            "email": "test@example.com",
            "role": "ADMIN",
        }
        self.client = TestClient(app)

    def tearDown(self):
        app.dependency_overrides.clear()

    def test_page_zero_rejected(self):
        response = self.client.get("/customers?page=0")
        self.assertEqual(response.status_code, 422)

    def test_negative_page_rejected(self):
        response = self.client.get("/customers?page=-1")
        self.assertEqual(response.status_code, 422)

    def test_page_size_zero_rejected(self):
        response = self.client.get("/customers?page_size=0")
        self.assertEqual(response.status_code, 422)

    def test_page_size_above_limit_rejected(self):
        response = self.client.get("/customers?page_size=101")
        self.assertEqual(response.status_code, 422)

    def test_invalid_risk_band_rejected(self):
        response = self.client.get("/customers?risk_band=CRITICAL")
        self.assertEqual(response.status_code, 422)

    def test_negative_credit_limit_rejected(self):
        response = self.client.get(
            "/customers?min_credit_limit=-100"
        )
        self.assertEqual(response.status_code, 422)

    def test_inverted_credit_range_rejected(self):
        response = self.client.get(
            "/customers?min_credit_limit=50000"
            "&max_credit_limit=10000"
        )
        self.assertEqual(response.status_code, 400)

    def test_invalid_sort_field_rejected(self):
        response = self.client.get(
            "/customers?sort_by=password"
        )
        self.assertEqual(response.status_code, 422)

    def test_invalid_sort_order_rejected(self):
        response = self.client.get(
            "/customers?sort_order=up"
        )
        self.assertEqual(response.status_code, 422)

    def test_invalid_customer_id_rejected(self):
        response = self.client.get("/customers/0")
        self.assertEqual(response.status_code, 422)

    def test_missing_customer_detail_returns_404(self):
        with patch(
            "src.api.routes.customers.get_customer_by_id",
            return_value=None
        ):
            response = self.client.get("/customers/999999")

        self.assertEqual(response.status_code, 404)

    def test_missing_customer_activity_returns_404(self):
        with patch(
            "src.api.routes.customers.get_customer_activity",
            return_value=None
        ):
            response = self.client.get(
                "/customers/999999/activity"
            )

        self.assertEqual(response.status_code, 404)

    def test_missing_customer_risk_returns_404(self):
        with patch(
            "src.api.routes.customers.get_customer_risk",
            return_value=None
        ):
            response = self.client.get(
                "/customers/999999/risk"
            )

        self.assertEqual(response.status_code, 404)

    def test_valid_filters_forwarded_to_service(self):
        mock_response = {
            "page": 2,
            "page_size": 10,
            "total_records": 0,
            "total_pages": 0,
            "items": [],
        }

        with patch(
            "src.api.routes.customers.get_customers",
            return_value=mock_response
        ) as mock_service:
            response = self.client.get(
                "/customers"
                "?page=2"
                "&page_size=10"
                "&risk_band=HIGH"
                "&has_payment_delay=true"
                "&min_credit_limit=10000"
                "&max_credit_limit=50000"
                "&sort_by=risk_score"
                "&sort_order=desc"
            )

        self.assertEqual(response.status_code, 200)

        mock_service.assert_called_once_with(
            page=2,
            page_size=10,
            risk_band="HIGH",
            has_payment_delay=True,
            min_credit_limit=10000.0,
            max_credit_limit=50000.0,
            sort_by="risk_score",
            sort_order="desc",
        )

    def test_analyst_cannot_delete_customer(self):
        app.dependency_overrides[get_current_user] = lambda: {
            "user_id": 2,
            "username": "analyst",
            "email": "analyst@example.com",
            "role": "ANALYST",
        }

        with patch(
            "src.api.routes.customers.delete_customer"
        ) as mock_delete:
            response = self.client.delete("/customers/1")

        self.assertEqual(response.status_code, 403)
        mock_delete.assert_not_called()


if __name__ == "__main__":
    unittest.main()
