"""OpenTelemetry OTLP HTTP exporter stubs."""

from enum import Enum

from ._log_exporter import OTLPLogExporter
from .metric_exporter import OTLPMetricExporter
from .trace_exporter import OTLPSpanExporter


class Compression(str, Enum):
    """Compression strategies supported by OTLP exporters."""

    NONE = "none"
    GZIP = "gzip"


__all__ = ["Compression", "OTLPLogExporter", "OTLPMetricExporter", "OTLPSpanExporter"]
