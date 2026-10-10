import unittest
from unittest.mock import MagicMock, patch

from mysql.connector import Error

from src.api.database import get_db_connection
from src.api.services.customer_crud_service import delete_customer


class TestDatabaseLogging(unittest.TestCase):

    def test_connection_failure_logged(self):
        with patch(
            "src.api.database.mysql.connector.connect",
            side_effect=Error("simulated failure")
        ), patch(
            "src.api.database.logger.error"
        ) as mock_log:

            with self.assertRaises(RuntimeError):
                get_db_connection()

        mock_log.assert_called_once()

        self.assertNotIn(
            "simulated failure",
            str(mock_log.call_args)
        )

    def test_delete_transaction_failure_logged_and_rolled_back(self):
        connection = MagicMock()
        cursor = connection.cursor.return_value

        cursor.execute.side_effect = RuntimeError(
            "simulated SQL failure"
        )

        with patch(
            "src.api.services.customer_crud_service.get_db_connection",
            return_value=connection
        ), patch(
            "src.api.services.customer_crud_service.logger.error"
        ) as mock_log:

            with self.assertRaises(RuntimeError):
                delete_customer(999999)

        mock_log.assert_called_once()
        connection.rollback.assert_called_once()

        self.assertNotIn(
            "simulated SQL failure",
            str(mock_log.call_args)
        )


if __name__ == "__main__":
    unittest.main()