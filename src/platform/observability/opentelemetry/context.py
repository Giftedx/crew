"""OpenTelemetry context stub."""

from __future__ import annotations

from typing import Any


class Context(dict[str, Any]):
    """Lightweight context mapping used in OpenTelemetry stubs."""


_KEY_REGISTRY: dict[str, str] = {}


_CONTEXT_STACK: list[Context] = []


def attach(context: Any) -> Any:
    """Attach a context to the stack and return a token for detaching."""
    if not isinstance(context, Context):
        context = Context(context) if isinstance(context, dict) else Context({"value": context})
    _CONTEXT_STACK.append(context)
    return len(_CONTEXT_STACK) - 1


def detach(token: Any) -> None:
    """Detach a previously attached context using the provided token."""
    try:
        index = int(token)
    except (TypeError, ValueError):  # pragma: no cover - defensive fallback
        return
    if 0 <= index < len(_CONTEXT_STACK):
        del _CONTEXT_STACK[index:]


def get_current() -> Context:
    """Return the current context, or an empty mapping if none attached."""
    if not _CONTEXT_STACK:
        return Context()
    return _CONTEXT_STACK[-1]


def create_key(name: str) -> str:
    """Return a unique key identifier for the provided logical name."""

    suffix = len(_KEY_REGISTRY) + 1
    key = f"{name}-{suffix}"
    _KEY_REGISTRY[name] = key
    return key


def set_value(key: str, value: Any, context: Context | dict | None = None) -> Context:
    """Return a new context derived from `context` with the given key value."""

    base = Context()
    if context:
        base.update(context)
    base[key] = value
    return base


def get_value(key: str, context: Any | None = None) -> Any:
    """Fetch a value from context by key."""

    ctx = context if context is not None else get_current()
    if isinstance(ctx, dict):
        return ctx.get(key)
    with_context = getattr(ctx, "values", None)
    if callable(with_context):  # pragma: no cover - defensive
        try:
            values = with_context()
        except Exception:  # pragma: no cover - defensive
            return None
        if isinstance(values, dict):
            return values.get(key)
    return None


__all__ = [
    "Context",
    "attach",
    "create_key",
    "detach",
    "get_current",
    "get_value",
    "set_value",
]
