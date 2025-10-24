"""Stub for OpenTelemetry SDK metrics views."""


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


__all__ = ["View"]
