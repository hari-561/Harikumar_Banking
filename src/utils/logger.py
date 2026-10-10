import logging
import os

from pathlib import Path
from logging.handlers import RotatingFileHandler


PROJECT_ROOT = Path(__file__).resolve().parents[2]

LOG_DIR = PROJECT_ROOT / "logs"

LOG_FILE = LOG_DIR / "banking_app.log"


def setup_logger(name: str) -> logging.Logger:
    """
    Configure and return an application logger.

    Features:
    - Console logging
    - Rotating file logging
    - Consistent log formatting
    - Prevent duplicate handlers
    """

    logger = logging.getLogger(name)

    if getattr(logger, "_banking_configured", False):
        return logger

    LOG_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    level_name = os.getenv(
        "LOG_LEVEL",
        "INFO"
    ).upper()

    log_level = getattr(
        logging,
        level_name,
        logging.INFO
    )

    logger.setLevel(log_level)

    logger.propagate = False

    formatter = logging.Formatter(
        fmt=(
            "%(asctime)s | "
            "%(levelname)-8s | "
            "%(name)s | "
            "%(message)s"
        ),
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    console_handler = logging.StreamHandler()

    console_handler.setLevel(log_level)

    console_handler.setFormatter(formatter)

    file_handler = RotatingFileHandler(
        filename=LOG_FILE,
        maxBytes=5 * 1024 * 1024,
        backupCount=5,
        encoding="utf-8"
    )

    file_handler.setLevel(log_level)

    file_handler.setFormatter(formatter)

    logger.addHandler(console_handler)

    logger.addHandler(file_handler)

    logger._banking_configured = True

    return logger

