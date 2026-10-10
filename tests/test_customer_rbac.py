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


class TestCustomerRBAC(unittest.TestCase):

    def tearDown(self):
        app.dependency_overrides.clear()

    def test_missing_token(self):
        response = client.get("/customers")

        self.assertEqual(response.status_code, 401)

    def test_invalid_token(self):
        response = client.get(
            "/customers",
            headers={
                "Authorization": "Bearer invalid.jwt.token"
            }
        )

        self.assertEqual(response.status_code, 401)

    def test_viewer_can_read_customers(self):
        app.dependency_overrides[get_current_user] = (
            lambda: mock_user("VIEWER")
        )

        with patch(
            "src.api.routes.customers.get_customers",
            return_value={
                "page": 1,
                "page_size": 20,
                "total_records": 0,
                "total_pages": 0,
                "customers": []
            }
        ):
            response = client.get("/customers")

        self.assertEqual(response.status_code, 200)

    def test_analyst_cannot_delete_customer(self):
        app.dependency_overrides[get_current_user] = (
            lambda: mock_user("ANALYST")
        )

        response = client.delete("/customers/1")

        self.assertEqual(response.status_code, 403)

    def test_viewer_cannot_delete_customer(self):
        app.dependency_overrides[get_current_user] = (
            lambda: mock_user("VIEWER")
        )

        response = client.delete("/customers/1")

        self.assertEqual(response.status_code, 403)

    def test_analyst_cannot_update_customer(self):
        app.dependency_overrides[get_current_user] = (
            lambda: mock_user("ANALYST")
        )

        response = client.put(
            "/customers/1",
            json={}
        )

        self.assertEqual(response.status_code, 403)

    def test_viewer_can_read_customers(self):
        app.dependency_overrides[get_current_user] = (
            lambda: mock_user("VIEWER")
        )

        with patch(
            "src.api.routes.customers.get_customers",
            return_value={
                "page": 1,
                "page_size": 20,
                "total_records": 0,
                "total_pages": 0,
                "items": []
            }
        ):
            response = client.get("/customers")

        self.assertEqual(response.status_code, 200)

    def test_viewer_cannot_create_customer(self):
        app.dependency_overrides[get_current_user] = (
            lambda: mock_user("VIEWER")
        )

        response = client.post(
            "/customers",
            json={}
        )

        self.assertEqual(response.status_code, 403)


if __name__ == "__main__":
    unittest.main()