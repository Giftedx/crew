from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, runtime_checkable


if TYPE_CHECKING:
    from collections.abc import Mapping


@runtime_checkable
class MetricLike(Protocol):
    def inc(self, value: float | int = 1) -> None: ...
    def set(self, value: float, labels: Mapping[str, str] | None = None) -> None: ...
    def observe(self, value: float, labels: Mapping[str, str] | None = None) -> None: ...


class MetricsFacade(Protocol):
    def counter(self, name: str, description: str | None = None) -> MetricLike: ...
    def gauge(self, name: str, description: str | None = None) -> MetricLike: ...
    def histogram(self, name: str, description: str | None = None) -> MetricLike: ...


__all__ = ["MetricLike", "MetricsFacade"]
