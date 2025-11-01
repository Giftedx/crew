"""Stub for OpenTelemetry SDK metrics views."""


class Aggregation:
    """Placeholder aggregation strategy."""

    def __init__(self, *args, **kwargs):  # pragma: no cover - stub
        pass


class ExponentialBucketHistogramAggregation(Aggregation):
    """Stub aggregation representing exponential bucket histogramming."""

    def __init__(self, max_size: int | None = None):  # pragma: no cover - stub
        super().__init__(max_size=max_size)


class View:
    """No-op view stub for metric aggregation configuration."""

    def __init__(
        self,
        instrument_type=None,
        instrument_name=None,
        instrument_unit=None,
        name=None,
        description=None,
        attribute_keys=None,
        aggregation=None,
    ):
        """Initialize stub view."""


__all__ = ["Aggregation", "ExponentialBucketHistogramAggregation", "View"]
