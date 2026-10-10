import unittest
from unittest.mock import patch

from src.api.routes.customers import (
    create_new_customer,
    update_existing_customer,
    delete_existing_customer,
)


class TestCustomerLogging(unittest.TestCase):

    def test_create_logs_success(self):
        result = {
            "status": "created",
            "customer_id": 30001,
            "risk_score": 25,
            "risk_band": "LOW",
        }

        with patch(
            "src.api.routes.customers.create_customer",
            return_value=result
        ), patch(
            "src.api.routes.customers.logger.info"
        ) as mock_log:

            response = create_new_customer(
                request=object()
            )

        self.assertEqual(response["customer_id"], 30001)
        mock_log.assert_called_once()

    def test_update_logs_success(self):
        result = {
            "status": "updated",
            "customer_id": 30001,
            "risk_score": 30,
            "risk_band": "MEDIUM",
        }

        with patch(
            "src.api.routes.customers.update_customer",
            return_value=result
        ), patch(
            "src.api.routes.customers.logger.info"
        ) as mock_log:

            response = update_existing_customer(
                request=object(),
                customer_id=30001
            )

        self.assertEqual(response["customer_id"], 30001)
        mock_log.assert_called_once()

    def test_delete_logs_success(self):
        result = {
            "status": "deleted",
            "customer_id": 30001,
        }

        with patch(
            "src.api.routes.customers.delete_customer",
            return_value=result
        ), patch(
            "src.api.routes.customers.logger.info"
        ) as mock_log:

            response = delete_existing_customer(
                customer_id=30001
            )

        self.assertEqual(response["customer_id"], 30001)
        mock_log.assert_called_once()

    def test_duplicate_create_not_logged_as_success(self):
        result = {
            "status": "duplicate",
            "customer_id": 30001,
        }

        with patch(
            "src.api.routes.customers.create_customer",
            return_value=result
        ), patch(
            "src.api.routes.customers.logger.info"
        ) as mock_log:

            from fastapi import HTTPException

            with self.assertRaises(HTTPException) as context:
                create_new_customer(request=object())

        self.assertEqual(context.exception.status_code, 409)
        mock_log.assert_not_called()


if __name__ == "__main__":
    unittest.main()