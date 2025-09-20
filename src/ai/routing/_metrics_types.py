from __future__ import annotations

from collections.abc import Mapping
from typing import Protocol, runtime_checkable


@runtime_checkable
class MetricLike(Protocol):
    def inc(self, value: float | int = 1) -> None: ...  # noqa: D401
    def set(self, value: float, labels: Mapping[str, str] | None = None) -> None: ...
    def observe(self, value: float, labels: Mapping[str, str] | None = None) -> None: ...


class MetricsFacade(Protocol):
    def counter(self, name: str, description: str | None = None) -> MetricLike: ...
    def gauge(self, name: str, description: str | None = None) -> MetricLike: ...
    def histogram(self, name: str, description: str | None = None) -> MetricLike: ...


__all__ = ["MetricLike", "MetricsFacade"]
