"""Logfire span helpers for pipeline instrumentation.

Lightweight wrappers to add Logfire spans when enabled, with no overhead when disabled.
"""
from __future__ import annotations
import logging
from typing import TYPE_CHECKING, Any
from platform.config.configuration import get_config
if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable
    from contextlib import AbstractContextManager
logger = logging.getLogger(__name__)
_LOGFIRE_AVAILABLE = False
_logfire: Any = None
try:
    import logfire as _logfire_import
    _logfire = _logfire_import
    _LOGFIRE_AVAILABLE = True
except Exception:
    pass

def is_logfire_enabled() -> bool:
    """Check if Logfire is enabled and available."""
    cfg = get_config()
    return bool(getattr(cfg, 'enable_logfire', False) and _LOGFIRE_AVAILABLE)

def span(name: str, **attributes: Any) -> AbstractContextManager[Any]:
    """Create a Logfire span if enabled, otherwise no-op context manager.

    Args:
        name: Span name
        **attributes: Additional span attributes

    Returns:
        Context manager for the span or no-op
    """
    if is_logfire_enabled() and _logfire is not None:
        try:
            return _logfire.span(name, **attributes)
        except Exception as exc:
            logger.debug('Logfire span creation failed: %s', exc)
    from contextlib import nullcontext
    return nullcontext()

async def with_span_async(name: str, coro: Callable[..., Awaitable[Any]], *args: Any, **kwargs: Any) -> Any:
    """Execute async function with Logfire span if enabled.

    Args:
        name: Span name
        coro: Async coroutine to execute
        *args: Positional args for coro
        **kwargs: Keyword args for coro

    Returns:
        Result of coro
    """
    if is_logfire_enabled() and _logfire is not None:
        try:
            with _logfire.span(name):
                return await coro(*args, **kwargs)
        except Exception as exc:
            logger.debug('Logfire span execution failed: %s', exc)
    return await coro(*args, **kwargs)

def set_span_attribute(key: str, value: Any) -> None:
    """Set attribute on current span if Logfire is enabled.

    Args:
        key: Attribute key
        value: Attribute value
    """
    if is_logfire_enabled() and _logfire is not None:
        try:
            from opentelemetry import trace
            current_span = trace.get_current_span()
            if current_span is not None:
                current_span.set_attribute(key, value)
        except Exception as exc:
            logger.debug('Failed to set span attribute: %s', exc)
__all__ = ['is_logfire_enabled', 'set_span_attribute', 'span', 'with_span_async']