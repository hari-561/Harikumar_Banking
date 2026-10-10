import unittest

from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from src.api.security.dependencies import get_current_user
from src.api.security.rbac import require_roles


test_app = FastAPI()


@test_app.get("/admin-only")
def admin_only(
    user: dict = Depends(require_roles("ADMIN"))
):
    return {"message": "Admin access granted"}


@test_app.get("/reports")
def reports(
    user: dict = Depends(
        require_roles("ADMIN", "ANALYST")
    )
):
    return {"message": "Reports access granted"}


@test_app.get("/dashboard")
def dashboard(
    user: dict = Depends(
        require_roles("ADMIN", "ANALYST", "VIEWER")
    )
):
    return {"message": "Dashboard access granted"}


client = TestClient(test_app)


class TestRBAC(unittest.TestCase):

    def tearDown(self):
        test_app.dependency_overrides.clear()

    def set_role(self, role):
        def mock_user():
            return {
                "user_id": 1,
                "username": "testuser",
                "email": "test@example.com",
                "role": role
            }

        test_app.dependency_overrides[
            get_current_user
        ] = mock_user

    def test_admin_can_access_admin_endpoint(self):
        self.set_role("ADMIN")

        response = client.get("/admin-only")

        self.assertEqual(response.status_code, 200)

    def test_analyst_cannot_access_admin_endpoint(self):
        self.set_role("ANALYST")

        response = client.get("/admin-only")

        self.assertEqual(response.status_code, 403)

    def test_viewer_cannot_access_admin_endpoint(self):
        self.set_role("VIEWER")

        response = client.get("/admin-only")

        self.assertEqual(response.status_code, 403)

    def test_analyst_can_access_reports(self):
        self.set_role("ANALYST")

        response = client.get("/reports")

        self.assertEqual(response.status_code, 200)

    def test_viewer_cannot_access_reports(self):
        self.set_role("VIEWER")

        response = client.get("/reports")

        self.assertEqual(response.status_code, 403)

    def test_viewer_can_access_dashboard(self):
        self.set_role("VIEWER")

        response = client.get("/dashboard")

        self.assertEqual(response.status_code, 200)

    def test_missing_token_returns_401(self):
        response = client.get("/admin-only")

        self.assertEqual(response.status_code, 401)

    def test_invalid_role_configuration(self):
        with self.assertRaises(ValueError):
            require_roles("SUPERADMIN")

    def test_empty_role_configuration(self):
        with self.assertRaises(ValueError):
            require_roles()


if __name__ == "__main__":
    unittest.main()