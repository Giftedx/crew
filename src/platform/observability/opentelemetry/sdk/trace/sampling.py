"""Minimal sampling stubs for OpenTelemetry compatibility in tests."""

from __future__ import annotations

from dataclasses import dataclass


class Decision:
    """Enumeration of sampling decisions."""

    DROP = 0
    RECORD_ONLY = 1
    RECORD_AND_SAMPLE = 2


@dataclass
class SamplingResult:
    """Simple sampling result container."""

    decision: int
    attributes: dict[str, object] | None = None
    tracestate: object | None = None


class Sampler:
    """Basic sampler stub returning deterministic sampling results."""

    def should_sample(self, *args, **kwargs) -> SamplingResult:  # pragma: no cover - stub
        return SamplingResult(Decision.RECORD_AND_SAMPLE)

    def get_description(self) -> str:  # pragma: no cover - stub
        return self.__class__.__name__


class TraceIdRatioBased(Sampler):
    """Sampler that includes traces according to a ratio."""

    TRACE_ID_LIMIT = (1 << 64) - 1

    def __init__(self, rate: float) -> None:
        self.rate = max(0.0, min(rate, 1.0))

    @staticmethod
    def get_bound_for_rate(rate: float) -> int:
        clamped = max(0.0, min(rate, 1.0))
        return int(clamped * (TraceIdRatioBased.TRACE_ID_LIMIT + 1))

    def should_sample(self, *args, **kwargs) -> SamplingResult:  # pragma: no cover - stub
        return SamplingResult(Decision.RECORD_AND_SAMPLE if self.rate > 0 else Decision.DROP)

    def get_description(self) -> str:  # pragma: no cover - stub
        return f"TraceIdRatioBased({self.rate:.3f})"


class ParentBasedTraceIdRatio(Sampler):
    """Simplified parent-based sampler delegating to a ratio sampler."""

    def __init__(self, rate: float, root: Sampler | None = None):
        self._ratio_sampler = TraceIdRatioBased(rate)
        self._root_sampler = root or self._ratio_sampler

    def should_sample(
        self, parent_context=None, *args, **kwargs
    ) -> SamplingResult:  # pragma: no cover - stub behaviour
        if parent_context is None:
            return self._root_sampler.should_sample(*args, **kwargs)
        return self._ratio_sampler.should_sample(*args, **kwargs)

    def get_description(self) -> str:  # pragma: no cover - stub behaviour
        return f"ParentBasedTraceIdRatio({self._ratio_sampler.get_description()})"


__all__ = [
    "Decision",
    "ParentBasedTraceIdRatio",
    "Sampler",
    "SamplingResult",
    "TraceIdRatioBased",
]
