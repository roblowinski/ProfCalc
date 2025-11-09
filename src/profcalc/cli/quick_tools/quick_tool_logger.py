"""quick_tool_logger.py

Shared logger utility for quick tools. Uses Python's logging module with a
rotating file handler to avoid unbounded log growth. Provide a small helper
`log_quick_tool_error(tool_name, message)` that other modules call.
"""
from __future__ import annotations

import logging
import logging.handlers
import os
from typing import Optional

LOG_FILE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
    "QuickToolErrors.log",
)


def _get_quick_tool_logger() -> logging.Logger:
    """Return a configured logger for quick tools (singleton-like)."""
    name = "profcalc.quick_tools"
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)
    # Use a rotating file handler to limit disk usage
    try:
        handler = logging.handlers.RotatingFileHandler(
            LOG_FILE, maxBytes=1_000_000, backupCount=5, encoding="utf-8"
        )
    except (OSError, IOError):
        # Best-effort fallback to stream handler if file cannot be opened
        handler = logging.StreamHandler()

    fmt = logging.Formatter(
        "[%(asctime)s] [%(name)s] %(levelname)s: %(message)s"
    )
    handler.setFormatter(fmt)
    logger.addHandler(handler)
    return logger


def log_quick_tool_error(
    tool_name: str, message: str, exc: Optional[BaseException] = None
) -> None:
    """Log an error for a quick tool.

    - tool_name: short identifier of the quick tool
    - message: human readable message
    - exc: optional exception to include traceback
    """
    logger = _get_quick_tool_logger()
    full_msg = f"[{tool_name}] {message}"
    if exc is not None:
        logger.exception(full_msg)
    else:
        logger.error(full_msg)
