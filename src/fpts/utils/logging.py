import logging
import sys
from typing import Optional

from pythonjsonlogger.json import JsonFormatter


def setup_logging(level: str = "INFO", *, json: bool = False) -> None:
    """
    Configure root logger for the application.
    This should be called once on startup.
    """
    if logging.getLogger().handlers:
        return

    handler = logging.StreamHandler(sys.stdout)
    log_level = getattr(logging, level.upper(), logging.INFO)

    if json:
        formatter = JsonFormatter(
            "%(asctime)s | %(levelname)s |  %(name)s | %(message)s | %(request_id)s"
        )

    else:
        formatter = logging.Formatter(
            fmt="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    root_logger.addHandler(handler)


def get_logger(name: Optional[str] = None) -> logging.Logger:
    return logging.getLogger(name or __name__)
