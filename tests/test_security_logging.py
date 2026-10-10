import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from src.api.main import app
from src.api.security.dependencies import get_current_user


client = TestClient(app)


class TestSecurityLogging(unittest.TestCase):

    def tearDown(self):
        app.dependency_overrides.clear()

    def test_failed_login_logged(self):
        with patch(
            "src.api.routes.auth.authenticate_user",
            return_value=None
        ), patch(
            "src.api.routes.auth.logger.warning"
        ) as mock_warning:

            response = client.post(
                "/auth/login",
                json={
                    "username": "invalid",
                    "password": "invalid"
                }
            )

        self.assertEqual(response.status_code, 401)
        mock_warning.assert_called_once()

        mock_warning.assert_called_once_with(
    "Login failed | reason=invalid_credentials_or_inactive_account"
)

    def test_successful_login_logged(self):
        fake_user = {
            "user_id": 123,
            "username": "testadmin",
            "role": "ADMIN"
        }

        with patch(
            "src.api.routes.auth.authenticate_user",
            return_value=fake_user
        ), patch(
            "src.api.routes.auth.create_access_token",
            return_value="mock-token"
        ), patch(
            "src.api.routes.auth.logger.info"
        ) as mock_info:

            response = client.post(
                "/auth/login",
                json={
                    "username": "testadmin",
                    "password": "secret-test-password"
                }
            )

        self.assertEqual(response.status_code, 200)
        mock_info.assert_called_once()

        logged_arguments = str(mock_info.call_args)
        self.assertNotIn("secret-test-password", logged_arguments)
        self.assertNotIn("mock-token", logged_arguments)

    def test_rbac_denial_logged(self):
        app.dependency_overrides[get_current_user] = lambda: {
            "user_id": 456,
            "username": "testviewer",
            "role": "VIEWER"
        }

        with patch(
            "src.api.security.rbac.logger.warning"
        ) as mock_warning:

            response = client.get("/export/customers")

        self.assertEqual(response.status_code, 403)
        mock_warning.assert_called_once()

        logged_arguments = str(mock_warning.call_args)
        self.assertIn("456", logged_arguments)
        self.assertIn("VIEWER", logged_arguments)


if __name__ == "__main__":
    unittest.main()