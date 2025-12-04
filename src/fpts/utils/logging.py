import logging
import sys
from typing import Optional


def setup_logging(level: str = "INFO") -> None:
    """
    Configure root logger for the application.
    This should be called once on startup.
    """
    if logging.getLogger().handlers:
        return

    log_level = getattr(logging, level.upper(), logging.INFO)

    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    root_logger.addHandler(handler)


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Get a loggere with a consistent configuration
    """
    return logging.getLogger(name or __name__)
