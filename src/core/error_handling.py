"""Standardized error handling utilities for consistent error management.

This module provides utilities for:
- Consistent error logging with proper context
- Standardized exception handling patterns
- Error recovery mechanisms
- Custom exception classes for application-specific errors
"""

from __future__ import annotations

import logging
import time
from collections.abc import Callable
from contextlib import contextmanager
from typing import Any, TypeVar

logger = logging.getLogger(__name__)


class UltimateDiscordBotError(Exception):
    """Base exception class for Ultimate Discord Intelligence Bot errors."""

    def __init__(self, message: str, context: dict[str, Any] | None = None):
        super().__init__(message)
        self.message = message
        self.context = context or {}

    def __str__(self) -> str:
        if self.context:
            context_str = ", ".join(f"{k}={v}" for k, v in self.context.items())
            return f"{self.message} ({context_str})"
        return self.message


class ConfigurationError(UltimateDiscordBotError):
    """Raised when there's a configuration-related error."""

    pass


class DatabaseError(UltimateDiscordBotError):
    """Raised when there's a database-related error."""

    pass


class ExternalServiceError(UltimateDiscordBotError):
    """Raised when an external service (API, etc.) fails."""

    pass


class ValidationError(UltimateDiscordBotError):
    """Raised when input validation fails."""

    pass


class ProcessingError(UltimateDiscordBotError):
    """Raised when content processing fails."""

    pass


def log_error(
    error: Exception,
    message: str | None = None,
    context: dict[str, Any] | None = None,
    level: int = logging.ERROR,
    logger_instance: logging.Logger | None = None,
) -> None:
    """Log an error with consistent formatting and context.

    Args:
        error: The exception that occurred
        message: Optional custom message to prepend
        context: Additional context to include in the log
        level: Logging level (default: ERROR)
        logger_instance: Specific logger to use (default: module logger)
    """
    log = logger_instance or logger

    # Build the log message
    log_message = f"{message}: {error}" if message else str(error)

    # Add context if provided
    if context:
        context_str = ", ".join(f"{k}={v}" for k, v in context.items())
        log_message = f"{log_message} [context: {context_str}]"

    # Log with appropriate level
    log.log(level, log_message, exc_info=True)


T = TypeVar("T")


def handle_error_safely(
    operation: Callable[[], T], fallback: T | None = None, error_message: str | None = None, reraise: bool = False
) -> T | None:
    """Execute an operation safely with error handling.

    Args:
        operation: The operation to execute
        fallback: Value to return if operation fails
        error_message: Custom error message
        reraise: Whether to re-raise the exception after logging

    Returns:
        Result of operation or fallback value
    """
    try:
        return operation()
    except Exception as e:
        log_error(e, message=error_message)
        if reraise:
            raise
        return fallback


@contextmanager
def error_context(context: dict[str, Any] | None = None):
    """Context manager that adds error context to any exceptions raised within.

    Args:
        context: Context to add to any exceptions
    """
    try:
        yield
    except UltimateDiscordBotError as e:
        # Add context to our custom exceptions
        if context:
            e.context.update(context)
        raise
    except Exception as e:
        # Wrap other exceptions in our base exception
        if context:
            raise UltimateDiscordBotError(str(e), context) from e
        raise


def retry_with_backoff(
    operation: Callable[[], T],
    max_attempts: int = 3,
    backoff_factor: float = 2.0,
    max_backoff: float = 60.0,
    exceptions: tuple[type[Exception], ...] = (Exception,),
) -> T:
    """Retry an operation with exponential backoff.

    Args:
        operation: The operation to retry
        max_attempts: Maximum number of attempts
        backoff_factor: Factor to multiply backoff by each attempt
        max_backoff: Maximum backoff time in seconds
        exceptions: Tuple of exception types to retry on

    Returns:
        Result of successful operation

    Raises:
        The last exception if all attempts fail
    """
    last_exception = None

    for attempt in range(max_attempts):
        try:
            return operation()
        except exceptions as e:
            last_exception = e

            if attempt < max_attempts - 1:
                # Calculate backoff time
                backoff_time = min(backoff_factor**attempt, max_backoff)
                sleep_time = backoff_time

                logger.warning(
                    f"Operation failed (attempt {attempt + 1}/{max_attempts}), retrying in {sleep_time:.2f}s: {e}"
                )
                time.sleep(sleep_time)
            else:
                logger.error(f"Operation failed after {max_attempts} attempts: {e}")
                raise

    # This should never be reached, but just in case
    if last_exception:
        raise last_exception
    raise RuntimeError("Unexpected error in retry logic")


def validate_and_raise(
    condition: bool,
    message: str,
    context: dict[str, Any] | None = None,
    exception_class: type[UltimateDiscordBotError] = ValidationError,
) -> None:
    """Validate a condition and raise an exception if it fails.

    Args:
        condition: The condition to check
        message: Error message if condition fails
        context: Additional context for the error
        exception_class: Exception class to raise
    """
    if not condition:
        raise exception_class(message, context)


__all__ = [
    "UltimateDiscordBotError",
    "ConfigurationError",
    "DatabaseError",
    "ExternalServiceError",
    "ValidationError",
    "ProcessingError",
    "log_error",
    "handle_error_safely",
    "error_context",
    "retry_with_backoff",
    "validate_and_raise",
]
