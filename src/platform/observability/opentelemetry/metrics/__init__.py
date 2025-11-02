"""Public metrics API stubs for OpenTelemetry."""

from __future__ import annotations

from collections.abc import Callable, Iterable
from typing import Any


CallbackT = Callable[..., Iterable[Any] | None]


class Instrument:
    """Base class for synchronous instruments."""

    def __init__(self, name: str, unit: str = "", description: str | None = None) -> None:
        self.name = name
        self.unit = unit
        self.description = description or ""

    def add(self, amount: Any, attributes: dict[str, Any] | None = None) -> None:  # pragma: no cover - stub behaviour
        return None

    def record(
        self, amount: Any, attributes: dict[str, Any] | None = None
    ) -> None:  # pragma: no cover - stub behaviour
        return None


class Counter(Instrument):
    """Counter stub that ignores measurements."""


class UpDownCounter(Instrument):
    """UpDownCounter stub that ignores measurements."""


class Histogram(Instrument):
    """Histogram stub that ignores measurements."""


class _Gauge(Instrument):
    """Synchronous gauge stub used by Logfire wrappers."""

    def set(self, amount: Any, attributes: dict[str, Any] | None = None) -> None:  # pragma: no cover - stub behaviour
        return None


class _ObservableInstrument(Instrument):
    """Base class for observable instruments."""

    def __init__(
        self,
        name: str,
        callbacks: Iterable[CallbackT] | None = None,
        unit: str = "",
        description: str | None = None,
    ) -> None:
        super().__init__(name, unit=unit, description=description)
        self.callbacks = list(callbacks or [])


class ObservableCounter(_ObservableInstrument):
    """Observable counter stub."""


class ObservableUpDownCounter(_ObservableInstrument):
    """Observable up/down counter stub."""


class ObservableGauge(_ObservableInstrument):
    """Observable gauge stub."""


class Meter:
    """Meter that produces instrument stubs."""

    def __init__(self, name: str, version: str | None = None, schema_url: str | None = None) -> None:
        self._name = name
        self._version = version
        self._schema_url = schema_url

    def create_counter(self, name: str, unit: str = "", description: str = "") -> Counter:
        return Counter(name, unit=unit, description=description)

    def create_up_down_counter(self, name: str, unit: str = "", description: str = "") -> UpDownCounter:
        return UpDownCounter(name, unit=unit, description=description)

    def create_histogram(self, name: str, unit: str = "", description: str = "") -> Histogram:
        return Histogram(name, unit=unit, description=description)

    def create_gauge(self, name: str, unit: str = "", description: str = "") -> _Gauge:
        return _Gauge(name, unit=unit, description=description)

    def create_observable_counter(
        self,
        name: str,
        callbacks: Iterable[CallbackT] | None = None,
        unit: str = "",
        description: str = "",
    ) -> ObservableCounter:
        return ObservableCounter(name, callbacks=callbacks, unit=unit, description=description)

    def create_observable_up_down_counter(
        self,
        name: str,
        callbacks: Iterable[CallbackT] | None = None,
        unit: str = "",
        description: str = "",
    ) -> ObservableUpDownCounter:
        return ObservableUpDownCounter(name, callbacks=callbacks, unit=unit, description=description)

    def create_observable_gauge(
        self,
        name: str,
        callbacks: Iterable[CallbackT] | None = None,
        unit: str = "",
        description: str = "",
    ) -> ObservableGauge:
        return ObservableGauge(name, callbacks=callbacks, unit=unit, description=description)


class MeterProvider:
    """Base meter provider returning stub meters."""

    def get_meter(
        self,
        name: str,
        version: str | None = None,
        schema_url: str | None = None,
        *args: Any,
        **kwargs: Any,
    ) -> Meter:
        return Meter(name, version=version, schema_url=schema_url)


class NoOpMeterProvider(MeterProvider):
    """Default meter provider used when metrics are disabled."""


_METER_PROVIDER: MeterProvider = NoOpMeterProvider()


def get_meter_provider() -> MeterProvider:
    return _METER_PROVIDER


def set_meter_provider(provider: MeterProvider) -> None:
    global _METER_PROVIDER
    _METER_PROVIDER = provider


def get_meter(name: str, version: str | None = None, schema_url: str | None = None) -> Meter:
    return get_meter_provider().get_meter(name, version=version, schema_url=schema_url)


__all__ = [
    "CallbackT",
    "Counter",
    "Histogram",
    "Instrument",
    "Meter",
    "MeterProvider",
    "NoOpMeterProvider",
    "ObservableCounter",
    "ObservableGauge",
    "ObservableUpDownCounter",
    "UpDownCounter",
    "_Gauge",
    "get_meter",
    "get_meter_provider",
    "set_meter_provider",
]
