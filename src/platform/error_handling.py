"""Error handling utilities for the platform."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any


if TYPE_CHECKING:
    from collections.abc import Callable


logger = logging.getLogger(__name__)


def handle_error_safely(func: Callable[[], Any], error_message: str) -> None:
    """Execute a function safely, logging any errors that occur.

    Args:
        func: Function to execute (typically a lambda)
        error_message: Message to log if execution fails
    """
    try:
        func()
    except Exception as e:
        logger.warning(f"{error_message}: {e}")


def log_error(error: Exception, context: dict[str, Any]) -> None:
    """Log an error with additional context information.

    Args:
        error: The exception that occurred
        context: Dictionary of context information to include in the log
    """
    logger.error("error_occurred", error=str(error), error_type=type(error).__name__, **context)
