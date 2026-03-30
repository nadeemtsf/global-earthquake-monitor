"""
Structured logging configuration for the Global Earthquake Monitor backend.

Call configure_logging() once at application startup (in main.py) to apply
a consistent, environment-aware log format across all loggers.
"""

from __future__ import annotations

import logging
import sys


def configure_logging(level: int = logging.INFO) -> None:
    """Configure root logger with a structured, timestamped format.

    Args:
        level: The minimum log level to emit. Defaults to INFO.
                Override via the LOG_LEVEL environment variable in .env.
    """
    formatter = logging.Formatter(
        fmt="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    # Avoid adding duplicate handlers on reload (e.g., uvicorn --reload)
    if not root_logger.handlers:
        root_logger.addHandler(handler)

    root_logger.setLevel(level)

    # Quieten noisy third-party loggers that would otherwise flood output
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
