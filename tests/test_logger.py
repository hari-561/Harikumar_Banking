import logging
import unittest

from logging.handlers import RotatingFileHandler

from src.utils.logger import setup_logger, LOG_FILE


class TestLogger(unittest.TestCase):

    def test_logger_created(self):
        logger = setup_logger("banking.test")

        self.assertIsInstance(
            logger,
            logging.Logger
        )

    def test_file_handler_exists(self):
        logger = setup_logger("banking.test")

        handlers = [
            handler
            for handler in logger.handlers
            if isinstance(
                handler,
                RotatingFileHandler
            )
        ]

        self.assertEqual(len(handlers), 1)

    def test_no_duplicate_handlers(self):
        logger = setup_logger("banking.test")

        initial_count = len(logger.handlers)

        setup_logger("banking.test")

        self.assertEqual(
            len(logger.handlers),
            initial_count
        )

    def test_log_file_created(self):
        logger = setup_logger("banking.test")

        logger.info(
            "Logging configuration test successful"
        )

        self.assertTrue(LOG_FILE.exists())


if __name__ == "__main__":
    unittest.main()