import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from src.api.main import app
from src.api.security.dependencies import get_current_user
from src.api.security.jwt_handler import (
    create_access_token,
    decode_access_token,
)

client = TestClient(app)


class TestAuthenticationSecurity(unittest.TestCase):

    def setUp(self):
        app.dependency_overrides.clear()

    def tearDown(self):
        app.dependency_overrides.clear()

    def test_valid_jwt(self):
        token = create_access_token(
            user_id=1,
            username="testadmin",
            role="ADMIN"
        )

        payload = decode_access_token(token)

        self.assertIsNotNone(payload)
        self.assertEqual(payload["sub"], "1")
        self.assertEqual(payload["role"], "ADMIN")

    def test_invalid_jwt(self):
        payload = decode_access_token(
            "invalid.jwt.token"
        )

        self.assertIsNone(payload)

    def test_missing_authorization_header(self):
        response = client.get("/auth/me")

        self.assertEqual(response.status_code, 401)

    def test_invalid_authorization_token(self):
        response = client.get(
            "/auth/me",
            headers={
                "Authorization": "Bearer invalid.jwt.token"
            }
        )

        self.assertEqual(response.status_code, 401)

    def test_valid_authenticated_user(self):
        def mock_current_user():
            return {
                "user_id": 1,
                "username": "testadmin",
                "email": "testadmin@example.com",
                "role": "ADMIN"
            }

        app.dependency_overrides[get_current_user] = mock_current_user

        response = client.get("/auth/me")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json()["username"],
            "testadmin"
        )

    def test_login_invalid_credentials(self):
        with patch(
            "src.api.routes.auth.authenticate_user",
            return_value=None
        ):
            response = client.post(
                "/auth/login",
                json={
                    "username": "wronguser",
                    "password": "wrongpassword"
                }
            )

        self.assertEqual(response.status_code, 401)

    def test_login_valid_credentials(self):
        mock_user = {
            "user_id": 1,
            "username": "testadmin",
            "email": "testadmin@example.com",
            "role": "ADMIN"
        }

        with patch(
            "src.api.routes.auth.authenticate_user",
            return_value=mock_user
        ):
            response = client.post(
                "/auth/login",
                json={
                    "username": "testadmin",
                    "password": "testpassword"
                }
            )

        self.assertEqual(response.status_code, 200)

        data = response.json()

        self.assertEqual(data["token_type"], "bearer")
        self.assertEqual(data["role"], "ADMIN")
        self.assertIn("access_token", data)

    def test_missing_login_password(self):
        response = client.post(
            "/auth/login",
            json={"username": "testadmin"}
        )

        self.assertEqual(response.status_code, 422)


if __name__ == "__main__":
    unittest.main()


    