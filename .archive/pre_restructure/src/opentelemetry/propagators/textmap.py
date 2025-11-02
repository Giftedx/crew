"""Minimal TextMapPropagator stub used for tests."""

from __future__ import annotations

from collections.abc import Mapping, MutableMapping
from typing import Any


class TextMapPropagator:
    """Simplified propagator base class compatible with OpenTelemetry API."""

    fields: tuple[str, ...] = ()

    def inject(
        self,
        carrier: MutableMapping[str, Any],
        context: Mapping[str, Any] | None = None,
        setter: Any | None = None,
    ) -> MutableMapping[str, Any]:
        """Inject context values into carrier; default implementation copies mapping."""

        if context is None:
            return carrier

        if setter is not None:
            for key, value in context.items():
                try:
                    setter.set(carrier, key, value)
                except AttributeError:
                    carrier[key] = value
            return carrier

        for key, value in context.items():
            carrier[key] = value
        return carrier

    def extract(
        self,
        carrier: Mapping[str, Any],
        context: Mapping[str, Any] | None = None,
        getter: Any | None = None,
    ) -> dict[str, Any]:
        """Extract context information from a carrier mapping."""

        base: dict[str, Any] = {}
        if context:
            base.update(context)

        if getter is not None:
            try:
                keys = getter.keys(carrier)
            except AttributeError:
                keys = []
            for key in keys:
                value: Any | None = None
                try:
                    value = getter.get(carrier, key)
                except AttributeError:
                    continue
                base[key] = value
            return base

        if isinstance(carrier, Mapping):
            base.update(dict(carrier.items()))
        return base


__all__ = ["TextMapPropagator"]
