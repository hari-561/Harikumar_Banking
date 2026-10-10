
import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "etl"))

import extract
import validate
import transform
import prepare_tables
import load
import incremental_load


class TestETLLogging(unittest.TestCase):

    def test_extraction_file_not_found_logging(self):
        with patch.object(extract.logger, "error") as mock_error:
            with self.assertRaises(FileNotFoundError):
                extract.extract_data(
                    "__missing_etl_logging_test__.xlsx"
                )

            self.assertTrue(mock_error.called)
            self.assertIn(
                "file_not_found",
                mock_error.call_args.args[0]
            )

    def test_validation_summary_logging(self):
        # Use a valid minimal dataset for all 13 checks.
        row = {
            "ID": 1,
            "LIMIT_BAL": 100000,
            "SEX": 1,
            "EDUCATION": 2,
            "MARRIAGE": 1,
            "AGE": 30,
            "default payment next month": 0,
        }

        for column in validate.REPAYMENT_COLUMNS:
            row[column] = 0

        for column in validate.BILL_COLUMNS:
            row[column] = 10000

        for column in validate.PAYMENT_COLUMNS:
            row[column] = 2000

        with patch.object(validate.logger, "info") as mock_info:
            report = validate.validate_data(pd.DataFrame([row]))

        self.assertEqual(len(report), 13)
        self.assertTrue(validate.validation_passed(report))
        self.assertTrue(
            any(
                "Data validation completed" in call.args[0]
                for call in mock_info.call_args_list
            )
        )

    def test_transformation_completion_logging(self):
        df = pd.DataFrame([{
            "ID": 1,
            "LIMIT_BAL": 100000,
            "SEX": 1,
            "EDUCATION": 2,
            "MARRIAGE": 1,
            "AGE": 30,
            "default payment next month": 0,
            **{
                column: 0
                for column in validate.REPAYMENT_COLUMNS
            },
            **{
                column: 10000
                for column in validate.BILL_COLUMNS
            },
            **{
                column: 2000
                for column in validate.PAYMENT_COLUMNS
            },
        }])

        with patch.object(transform.logger, "info") as mock_info:
            result = transform.transform_data(df)

        self.assertEqual(len(result), 1)
        self.assertTrue(
            any(
                "Transformation completed" in call.args[0]
                for call in mock_info.call_args_list
            )
        )

    def test_table_preparation_reconciliation_logging(self):
        df = pd.DataFrame([{
            "customer_id": 1,
            "gender_code": 1,
            "education_code": 2,
            "marital_status_code": 1,
            "age": 30,
            "credit_limit": 100000,
            "delay_month_count": 0,
            "max_delay_status": 0,
            "has_payment_delay": False,
            "total_bill_amount_6m": 60000,
            "average_bill_amount_6m": 10000,
            "total_payment_amount_6m": 12000,
            "average_payment_amount_6m": 2000,
            "latest_utilization_ratio": 0.1,
            "default_next_month": 0,
            **{
                f"repayment_status_{m}": 0
                for m in [
                    "sep", "aug", "jul",
                    "jun", "may", "apr"
                ]
            },
            **{
                f"bill_amount_{m}": 10000
                for m in [
                    "sep", "aug", "jul",
                    "jun", "may", "apr"
                ]
            },
            **{
                f"payment_amount_{m}": 2000
                for m in [
                    "sep", "aug", "jul",
                    "jun", "may", "apr"
                ]
            },
        }])

        with patch.object(
            prepare_tables.logger, "info"
        ) as mock_info:
            customers, profiles, monthly = (
                prepare_tables.prepare_database_tables(df)
            )

        self.assertEqual(len(customers), 1)
        self.assertEqual(len(profiles), 1)
        self.assertEqual(len(monthly), 6)

        self.assertTrue(
            any(
                "Table preparation reconciliation passed"
                in call.args[0]
                for call in mock_info.call_args_list
            )
        )

    def test_database_connection_failure_logging(self):
        from mysql.connector import Error

        with patch.object(
            load.mysql.connector,
            "connect",
            side_effect=Error("Simulated failure")
        ):
            with patch.object(
                load.logger, "error"
            ) as mock_error:
                with self.assertRaises(ConnectionError):
                    load.get_connection()

        self.assertTrue(mock_error.called)
        self.assertIn(
            "connection failed",
            mock_error.call_args.args[0]
        )

    def test_incremental_no_changes_logging(self):
        df = pd.DataFrame({
            "customer_id": [1, 2]
        })

        empty = pd.DataFrame({
            "customer_id": pd.Series(dtype="int64")
        })

        connection = MagicMock()
        connection.is_connected.return_value = True

        with (
            patch.object(
                incremental_load,
                "extract_data",
                return_value=df
            ),
            patch.object(
                incremental_load,
                "validate_data",
                return_value=pd.DataFrame()
            ),
            patch.object(
                incremental_load,
                "validation_passed",
                return_value=True
            ),
            patch.object(
                incremental_load,
                "transform_data",
                return_value=df
            ),
            patch.object(
                incremental_load,
                "fetch_existing_customers",
                return_value=df
            ),
            patch.object(
                incremental_load,
                "detect_changes",
                return_value=(empty, empty, df)
            ),
            patch.object(
                incremental_load,
                "get_connection",
                return_value=connection
            ),
            patch.object(
                incremental_load,
                "create_audit_record",
                return_value=42
            ),
            patch.object(
                incremental_load,
                "complete_audit_record"
            ),
            patch.object(
                incremental_load.logger,
                "info"
            ) as mock_info
        ):
            incremental_load.run_incremental_pipeline(
                "mock_source.xls"
            )

        connection.commit.assert_called_once()

        self.assertTrue(
            any(
                "Database load skipped" in call.args[0]
                for call in mock_info.call_args_list
            )
        )

        self.assertTrue(
            any(
                "Incremental transaction committed"
                in call.args[0]
                for call in mock_info.call_args_list
            )
        )


if __name__ == "__main__":
    unittest.main()
