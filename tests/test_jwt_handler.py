import unittest

from src.api.security.jwt_handler import (
    create_access_token,
    decode_access_token
)


class TestJWTHandler(unittest.TestCase):

    def test_create_and_decode_token(self):

        token = create_access_token(
            user_id=1,
            username="testadmin",
            role="ADMIN"
        )

        payload = decode_access_token(token)

        self.assertIsNotNone(payload)
        self.assertEqual(payload["sub"], "1")
        self.assertEqual(payload["username"], "testadmin")
        self.assertEqual(payload["role"], "ADMIN")
        self.assertEqual(payload["type"], "access")

    def test_invalid_token(self):

        result = decode_access_token(
            "invalid.jwt.token"
        )

        self.assertIsNone(result)

    def test_modified_token(self):

        token = create_access_token(
            user_id=1,
            username="testadmin",
            role="ADMIN"
        )

        modified_token = token[:-1] + (
            "A" if token[-1] != "A" else "B"
        )

        result = decode_access_token(
            modified_token
        )

        self.assertIsNone(result)

    def test_expired_token(self):

        import jwt

        from datetime import datetime, timedelta, timezone

        from src.api.security.jwt_handler import (
            JWT_SECRET_KEY,
            JWT_ALGORITHM
        )

        expired_payload = {
            "sub": "1",
            "type": "access",
            "iat": datetime.now(timezone.utc)
                - timedelta(hours=2),
            "nbf": datetime.now(timezone.utc)
                - timedelta(hours=2),
            "exp": datetime.now(timezone.utc)
                - timedelta(hours=1)
        }

        token = jwt.encode(
            expired_payload,
            JWT_SECRET_KEY,
            algorithm=JWT_ALGORITHM
        )

        self.assertIsNone(
            decode_access_token(token)
        )


if __name__ == "__main__":
    unittest.main()