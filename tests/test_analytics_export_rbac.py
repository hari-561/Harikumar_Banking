import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from src.api.main import app
from src.api.security.dependencies import get_current_user


client = TestClient(app)


def mock_user(role):
    return {
        "user_id": 1,
        "username": "testuser",
        "email": "test@example.com",
        "role": role
    }


class TestAnalyticsExportRBAC(unittest.TestCase):

    def tearDown(self):
        app.dependency_overrides.clear()

    def set_role(self, role):
        app.dependency_overrides[get_current_user] = (
            lambda: mock_user(role)
        )

    def test_analytics_requires_login(self):
        response = client.get("/analytics/summary")
        self.assertEqual(response.status_code, 401)

    def test_export_requires_login(self):
        response = client.get("/export/customers")
        self.assertEqual(response.status_code, 401)

    def test_viewer_can_access_analytics(self):
        self.set_role("VIEWER")

        with patch(
            "src.api.routes.analytics.get_risk_distribution",
            return_value=[]
        ):
            response = client.get(
                "/analytics/risk-distribution"
            )

        self.assertEqual(response.status_code, 200)

    def test_analyst_can_access_analytics(self):
        self.set_role("ANALYST")

        with patch(
            "src.api.routes.analytics.get_monthly_trends",
            return_value=[]
        ):
            response = client.get(
                "/analytics/monthly-trends"
            )

        self.assertEqual(response.status_code, 200)

    def test_viewer_cannot_export(self):
        self.set_role("VIEWER")

        response = client.get("/export/customers")

        self.assertEqual(response.status_code, 403)

    def test_analyst_can_export(self):
        self.set_role("ANALYST")

        with patch(
            "src.api.routes.export.get_customers_for_export",
            return_value=[]
        ):
            response = client.get("/export/customers")

        self.assertEqual(response.status_code, 200)
        self.assertIn(
            "text/csv",
            response.headers["content-type"]
        )

    def test_admin_can_export(self):
        self.set_role("ADMIN")

        with patch(
            "src.api.routes.export.get_customers_for_export",
            return_value=[]
        ):
            response = client.get("/export/customers")

        self.assertEqual(response.status_code, 200)


if __name__ == "__main__":
    unittest.main()