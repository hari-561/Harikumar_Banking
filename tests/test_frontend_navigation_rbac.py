import unittest

from src.frontend.components.shell import PAGE_ROLES


class TestFrontendNavigationRBAC(unittest.TestCase):

    def test_admin_has_six_pages(self):
        allowed = [
            page for page, roles in PAGE_ROLES.items()
            if "ADMIN" in roles
        ]
        self.assertEqual(len(allowed), 6)

    def test_analyst_cannot_manage_customers(self):
        self.assertNotIn(
            "ANALYST",
            PAGE_ROLES["Customer Management"]
        )

    def test_viewer_cannot_export(self):
        self.assertNotIn(
            "VIEWER",
            PAGE_ROLES["Reports & Export"]
        )

    def test_viewer_can_explore_customers(self):
        self.assertIn(
            "VIEWER",
            PAGE_ROLES["Customer Explorer"]
        )


if __name__ == "__main__":
    unittest.main()