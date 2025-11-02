"""Minimal OpenTelemetry propagate API used for tests."""

from __future__ import annotations

from collections.abc import Mapping, MutableMapping
from typing import Any

from .context import get_current
from .propagators.textmap import TextMapPropagator


class _DefaultTextMapPropagator(TextMapPropagator):
    """Fallback propagator that operates on plain dictionaries."""

    def inject(
        self,
        carrier: MutableMapping[str, Any],
        context: Mapping[str, Any] | None = None,
        setter: Any | None = None,
    ) -> MutableMapping[str, Any]:
        context = context or get_current()
        if not isinstance(carrier, MutableMapping):
            return carrier
        if setter is not None:
            try:
                for key, value in context.items():
                    setter.set(carrier, key, value)
                return carrier
            except AttributeError:  # pragma: no cover - defensive
                pass
        for key, value in context.items():
            carrier[key] = value
        return carrier

    def extract(
        self,
        carrier: Mapping[str, Any] | MutableMapping[str, Any],
        context: Mapping[str, Any] | None = None,
        getter: Any | None = None,
    ) -> dict[str, Any]:
        base: dict[str, Any] = {}
        if context:
            base.update(context)

        if getter is not None:
            try:
                keys = getter.keys(carrier)
            except AttributeError:  # pragma: no cover - defensive
                keys = []
            for key in keys:
                try:
                    base[key] = getter.get(carrier, key)
                except AttributeError:  # pragma: no cover - defensive
                    continue
            return base

        if isinstance(carrier, Mapping):
            base.update(dict(carrier.items()))
        return base


_GLOBAL_TEXTMAP: TextMapPropagator = _DefaultTextMapPropagator()


def get_global_textmap() -> TextMapPropagator:
    """Return the currently configured text map propagator."""

    return _GLOBAL_TEXTMAP


def set_global_textmap(propagator: TextMapPropagator) -> None:
    """Set the global text map propagator used for inject/extract."""

    global _GLOBAL_TEXTMAP
    _GLOBAL_TEXTMAP = propagator


def inject(
    carrier: MutableMapping[str, Any],
    context: Mapping[str, Any] | None = None,
    setter: Any | None = None,
) -> MutableMapping[str, Any]:
    """Inject the current context into the provided carrier."""

    return _GLOBAL_TEXTMAP.inject(carrier, context=context, setter=setter)


def extract(
    carrier: Mapping[str, Any] | MutableMapping[str, Any],
    context: Mapping[str, Any] | None = None,
    getter: Any | None = None,
) -> dict[str, Any]:
    """Extract context from the provided carrier."""

    return _GLOBAL_TEXTMAP.extract(carrier, context=context, getter=getter)


__all__ = [
    "extract",
    "get_global_textmap",
    "inject",
    "set_global_textmap",
]
