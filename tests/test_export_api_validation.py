
import csv
import io
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from src.api.main import app
from src.api.security.dependencies import get_current_user


SAMPLE_ROW = {
    "customer_id": 101,
    "gender": "Male",
    "education": "University",
    "marital_status": "Single",
    "age": 30,
    "credit_limit": 100000.0,
    "delay_month_count": 2,
    "max_delay_status": 2,
    "has_payment_delay": True,
    "total_bill_amount_6m": 60000.0,
    "average_bill_amount_6m": 10000.0,
    "total_payment_amount_6m": 30000.0,
    "average_payment_amount_6m": 5000.0,
    "latest_utilization_ratio": 0.4,
    "payment_to_bill_ratio": 0.5,
    "risk_score": 6,
    "risk_band": "HIGH",
    "rule_version": "v1",
}

EXPECTED_HEADERS = list(SAMPLE_ROW.keys())


class TestExportAPIValidation(unittest.TestCase):

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

    def export_with_rows(self, rows, params=None):
        with patch(
            "src.api.routes.export.get_customers_for_export",
            return_value=rows
        ) as mock_service:
            response = self.client.get(
                "/export/customers",
                params=params
            )
        return response, mock_service

    def parse_csv(self, response):
        return list(csv.DictReader(io.StringIO(response.text)))

    def test_export_success(self):
        response, _ = self.export_with_rows([SAMPLE_ROW])

        self.assertEqual(response.status_code, 200)
        self.assertIn(
            "text/csv",
            response.headers["content-type"]
        )

    def test_export_filename(self):
        response, _ = self.export_with_rows([SAMPLE_ROW])

        self.assertIn(
            "customers_export.csv",
            response.headers["content-disposition"]
        )

    def test_csv_headers(self):
        response, _ = self.export_with_rows([SAMPLE_ROW])

        reader = csv.reader(io.StringIO(response.text))
        headers = next(reader)

        self.assertEqual(headers, EXPECTED_HEADERS)

    def test_csv_row_values(self):
        response, _ = self.export_with_rows([SAMPLE_ROW])
        rows = self.parse_csv(response)

        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["customer_id"], "101")
        self.assertEqual(rows[0]["risk_band"], "HIGH")
        self.assertEqual(rows[0]["risk_score"], "6")
        self.assertEqual(rows[0]["credit_limit"], "100000.0")

    def test_multiple_csv_rows(self):
        second_row = {
            **SAMPLE_ROW,
            "customer_id": 102,
            "risk_band": "LOW",
            "risk_score": 1,
        }

        response, _ = self.export_with_rows(
            [SAMPLE_ROW, second_row]
        )

        rows = self.parse_csv(response)

        self.assertEqual(len(rows), 2)
        self.assertEqual(
            [row["customer_id"] for row in rows],
            ["101", "102"]
        )

    def test_empty_export_has_headers(self):
        response, _ = self.export_with_rows([])

        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.parse_csv(response), [])

        headers = next(
            csv.reader(io.StringIO(response.text))
        )
        self.assertEqual(headers, EXPECTED_HEADERS)

    def test_filter_parameters_forwarded(self):
        params = {
            "risk_band": "HIGH",
            "has_payment_delay": "true",
            "min_credit_limit": "10000",
            "max_credit_limit": "100000",
            "sort_by": "risk_score",
            "sort_order": "desc",
        }

        response, mock_service = self.export_with_rows(
            [SAMPLE_ROW],
            params=params
        )

        self.assertEqual(response.status_code, 200)

        mock_service.assert_called_once_with(
            risk_band="HIGH",
            has_payment_delay=True,
            min_credit_limit=10000.0,
            max_credit_limit=100000.0,
            sort_by="risk_score",
            sort_order="desc",
        )

    def test_invalid_risk_band_rejected(self):
        with patch(
            "src.api.routes.export.get_customers_for_export"
        ) as mock_service:
            response = self.client.get(
                "/export/customers?risk_band=CRITICAL"
            )

        self.assertEqual(response.status_code, 422)
        mock_service.assert_not_called()

    def test_negative_credit_limit_rejected(self):
        response = self.client.get(
            "/export/customers?min_credit_limit=-1"
        )
        self.assertEqual(response.status_code, 422)

    def test_inverted_credit_range_rejected(self):
        response = self.client.get(
            "/export/customers"
            "?min_credit_limit=90000"
            "&max_credit_limit=10000"
        )
        self.assertEqual(response.status_code, 400)

    def test_invalid_sort_order_rejected(self):
        response = self.client.get(
            "/export/customers?sort_order=random"
        )
        self.assertEqual(response.status_code, 422)

    def test_invalid_sort_field_rejected(self):
        response = self.client.get(
            "/export/customers?sort_by=password"
        )
        self.assertEqual(response.status_code, 422)

    def test_viewer_cannot_export(self):
        self.set_role("VIEWER")

        with patch(
            "src.api.routes.export.get_customers_for_export"
        ) as mock_service:
            response = self.client.get("/export/customers")

        self.assertEqual(response.status_code, 403)
        mock_service.assert_not_called()

    def test_analyst_can_export(self):
        self.set_role("ANALYST")

        response, _ = self.export_with_rows([SAMPLE_ROW])

        self.assertEqual(response.status_code, 200)

    def test_missing_token_rejected(self):
        app.dependency_overrides.clear()

        response = self.client.get("/export/customers")

        self.assertEqual(response.status_code, 401)

    def test_invalid_token_rejected(self):
        app.dependency_overrides.clear()

        response = self.client.get(
            "/export/customers",
            headers={
                "Authorization": "Bearer invalid.jwt.token"
            }
        )

        self.assertEqual(response.status_code, 401)


if __name__ == "__main__":
    unittest.main()
