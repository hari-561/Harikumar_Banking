
import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

import jwt
from fastapi.testclient import TestClient

from src.api.main import app
from src.api.security.jwt_handler import (
    JWT_ALGORITHM,
    JWT_SECRET_KEY,
    create_access_token,
    decode_access_token,
)


def make_token(**changes):
    now = datetime.now(timezone.utc)
    payload = {
        "sub": "1",
        "username": "testadmin",
        "role": "ADMIN",
        "iat": now,
        "nbf": now,
        "exp": now + timedelta(minutes=30),
        "type": "access",
    }
    payload.update(changes)
    return jwt.encode(
        payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM
    )


class TestAuthAPIEdgeCases(unittest.TestCase):

    def setUp(self):
        app.dependency_overrides.clear()
        self.client = TestClient(app)

    def tearDown(self):
        app.dependency_overrides.clear()

    def test_missing_password(self):
        response = self.client.post(
            "/auth/login",
            json={"username": "testadmin"}
        )
        self.assertEqual(response.status_code, 422)

    def test_empty_username(self):
        response = self.client.post(
            "/auth/login",
            json={"username": "", "password": "test123"}
        )
        self.assertEqual(response.status_code, 422)

    def test_empty_password(self):
        response = self.client.post(
            "/auth/login",
            json={"username": "testadmin", "password": ""}
        )
        self.assertEqual(response.status_code, 422)

    def test_login_invalid_credentials(self):
        with patch(
            "src.api.routes.auth.authenticate_user",
            return_value=None
        ):
            response = self.client.post(
                "/auth/login",
                json={
                    "username": "wrong",
                    "password": "wrong"
                }
            )

        self.assertEqual(response.status_code, 401)
        self.assertEqual(
            response.headers.get("www-authenticate"),
            "Bearer"
        )

    def test_login_response_expiry(self):
        user = {
            "user_id": 1,
            "username": "testadmin",
            "role": "ADMIN",
        }

        with patch(
            "src.api.routes.auth.authenticate_user",
            return_value=user
        ):
            response = self.client.post(
                "/auth/login",
                json={
                    "username": "testadmin",
                    "password": "test123"
                }
            )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["token_type"], "bearer")
        self.assertGreater(data["expires_in"], 0)
        self.assertEqual(
            decode_access_token(data["access_token"])["sub"],
            "1"
        )

    def test_expired_token_rejected(self):
        token = make_token(
            iat=datetime.now(timezone.utc) - timedelta(hours=2),
            nbf=datetime.now(timezone.utc) - timedelta(hours=2),
            exp=datetime.now(timezone.utc) - timedelta(hours=1),
        )
        self.assertIsNone(decode_access_token(token))

    def test_future_token_rejected(self):
        token = make_token(
            nbf=datetime.now(timezone.utc) + timedelta(hours=1)
        )
        self.assertIsNone(decode_access_token(token))

    def test_missing_expiration_rejected(self):
        now = datetime.now(timezone.utc)
        payload = {
            "sub": "1",
            "iat": now,
            "nbf": now,
            "type": "access",
        }
        token = jwt.encode(
            payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM
        )
        self.assertIsNone(decode_access_token(token))

    def test_wrong_token_type_rejected(self):
        token = make_token(type="refresh")
        self.assertIsNone(decode_access_token(token))

    def test_invalid_subject_rejected(self):
        token = make_token(sub="not-a-number")
        self.assertIsNone(decode_access_token(token))

    def test_zero_subject_rejected(self):
        token = make_token(sub="0")
        self.assertIsNone(decode_access_token(token))

    def test_modified_signature_rejected(self):
        token = make_token()
        parts = token.split(".")
        parts[1] = (
            "A" if parts[1][0] != "A" else "B"
        ) + parts[1][1:]
        modified = ".".join(parts)
        self.assertIsNone(decode_access_token(modified))

    def test_auth_me_without_token(self):
        response = self.client.get("/auth/me")
        self.assertEqual(response.status_code, 401)

    def test_auth_me_expired_token(self):
        token = make_token(
            iat=datetime.now(timezone.utc) - timedelta(hours=2),
            nbf=datetime.now(timezone.utc) - timedelta(hours=2),
            exp=datetime.now(timezone.utc) - timedelta(hours=1),
        )
        response = self.client.get(
            "/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        self.assertEqual(response.status_code, 401)

    def test_auth_me_invalid_scheme(self):
        response = self.client.get(
            "/auth/me",
            headers={"Authorization": "Basic abc123"}
        )
        self.assertEqual(response.status_code, 401)

    def test_inactive_database_user_rejected(self):
        token = create_access_token(1, "testadmin", "ADMIN")

        connection = MagicMock()
        cursor = connection.cursor.return_value
        cursor.fetchone.return_value = {
            "user_id": 1,
            "username": "testadmin",
            "email": "test@example.com",
            "role": "ADMIN",
            "is_active": False,
        }

        with patch(
            "src.api.security.dependencies.get_db_connection",
            return_value=connection
        ):
            response = self.client.get(
                "/auth/me",
                headers={
                    "Authorization": f"Bearer {token}"
                }
            )

        self.assertEqual(response.status_code, 401)
        cursor.close.assert_called_once()
        connection.close.assert_called_once()

    def test_missing_database_user_rejected(self):
        token = create_access_token(1, "testadmin", "ADMIN")

        connection = MagicMock()
        cursor = connection.cursor.return_value
        cursor.fetchone.return_value = None

        with patch(
            "src.api.security.dependencies.get_db_connection",
            return_value=connection
        ):
            response = self.client.get(
                "/auth/me",
                headers={
                    "Authorization": f"Bearer {token}"
                }
            )

        self.assertEqual(response.status_code, 401)
        cursor.close.assert_called_once()
        connection.close.assert_called_once()

    def test_database_role_overrides_token_role(self):
        token = create_access_token(1, "testuser", "ADMIN")

        connection = MagicMock()
        cursor = connection.cursor.return_value
        cursor.fetchone.return_value = {
            "user_id": 1,
            "username": "testuser",
            "email": "test@example.com",
            "role": "VIEWER",
            "is_active": True,
        }

        with patch(
            "src.api.security.dependencies.get_db_connection",
            return_value=connection
        ):
            response = self.client.get(
                "/auth/me",
                headers={
                    "Authorization": f"Bearer {token}"
                }
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["role"], "VIEWER")
        cursor.close.assert_called_once()
        connection.close.assert_called_once()


if __name__ == "__main__":
    unittest.main()
