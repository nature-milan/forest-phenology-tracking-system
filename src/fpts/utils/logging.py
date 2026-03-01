from __future__ import annotations

import contextvars
import logging
import sys

try:
    from pythonjsonlogger.json import JsonFormatter
except ImportError:
    JsonFormatter = None


# Request ID context handling
_request_id_ctx: contextvars.ContextVar[str] = contextvars.ContextVar("request_id", default="-")


def set_request_id(request_id: str) -> None:
    _request_id_ctx.set(request_id)


def get_request_id() -> str:
    return _request_id_ctx.get()


class RequestIdFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = get_request_id()
        return True


class LoggerPrefixFilter(logging.Filter):
    """
    Allows only loggers starting with a given prefix.
    Example: prefix="fpts.cache"
    """

    def __init__(self, prefix: str) -> None:
        super().__init__()
        self.prefix = prefix

    def filter(self, record: logging.LogRecord) -> bool:
        return record.name.startswith(self.prefix)


def _parse_level(level: str) -> int:
    return getattr(logging, level.upper(), logging.INFO)


def setup_logging(
    *,
    level: str = "INFO",
    json: bool = True,
    cache_debug: bool = True,
) -> None:
    """
    Production-grade logging setup:

    - Root logger at app level (INFO by default)
    - Main handler at app level
    - Dedicated DEBUG handler only for fpts.cache*
    - Uvicorn logs routed through root
    """

    app_level = _parse_level(level)

    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.setLevel(app_level)

    if json:
        if JsonFormatter is None:
            raise RuntimeError("python-json-logger must be installed for JSON logging.")

        formatter: logging.Formatter = JsonFormatter(
            "%(asctime)s | %(levelname)s | %(name)s | %(message)s | %(request_id)s"
        )
    else:
        formatter = logging.Formatter(
            "%(asctime)s | %(levelname)s | %(name)s | %(message)s | %(request_id)s"
        )

    # Main handler (clean prod logs)
    main_handler = logging.StreamHandler(sys.stdout)
    main_handler.setLevel(app_level)
    main_handler.addFilter(RequestIdFilter())
    main_handler.setFormatter(formatter)
    root_logger.addHandler(main_handler)

    # Cache-only debug handler
    if cache_debug:
        cache_handler = logging.StreamHandler(sys.stdout)
        cache_handler.setLevel(logging.DEBUG)
        cache_handler.addFilter(RequestIdFilter())
        cache_handler.addFilter(LoggerPrefixFilter("fpts.cache"))
        cache_handler.setFormatter(formatter)
        root_logger.addHandler(cache_handler)

        logging.getLogger("fpts.cache").setLevel(logging.DEBUG)

    # Ensure uvicorn logs use root config
    for name in ("uvicorn", "uvicorn.error", "uvicorn.access"):
        uv = logging.getLogger(name)
        uv.handlers.clear()
        uv.propagate = True
        uv.setLevel(app_level)


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
