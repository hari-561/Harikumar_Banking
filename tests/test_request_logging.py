import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from src.api.main import app


client = TestClient(app)


class TestRequestLogging(unittest.TestCase):

    def test_health_request_logged(self):
        with patch(
            "src.api.middleware.request_logging.logger.info"
        ) as mock_info:

            response = client.get("/health")

        self.assertEqual(response.status_code, 200)
        mock_info.assert_called()

        args = mock_info.call_args.args

        self.assertEqual(args[1], "GET")
        self.assertEqual(args[2], "/health")
        self.assertEqual(args[3], 200)

    def test_missing_token_logged(self):
        with patch(
            "src.api.middleware.request_logging.logger.warning"
        ) as mock_warning:

            response = client.get("/analytics/summary")

        self.assertEqual(response.status_code, 401)
        mock_warning.assert_called()

        args = mock_warning.call_args.args

        self.assertEqual(args[1], "GET")
        self.assertEqual(args[2], "/analytics/summary")
        self.assertEqual(args[3], 401)

    def test_query_parameters_not_logged(self):
        with patch(
            "src.api.middleware.request_logging.logger.info"
        ) as mock_info:

            response = client.get(
                "/health?private_value=do_not_log"
            )

        self.assertEqual(response.status_code, 200)

        logged_arguments = str(
            mock_info.call_args.args
        )

        self.assertNotIn(
            "do_not_log",
            logged_arguments
        )


if __name__ == "__main__":
    unittest.main()