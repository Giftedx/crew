"""
Distributed tracing and performance profiling for the Ultimate Discord Intelligence Bot.

Provides comprehensive tracing capabilities with performance profiling, span management,
and integration with external tracing systems like Jaeger, Zipkin, and OpenTelemetry.
"""

import contextvars
import logging
import time
import uuid
from collections.abc import AsyncGenerator, Generator
from contextlib import asynccontextmanager, contextmanager
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

import psutil


logger = logging.getLogger(__name__)

# Context variable for tracing
_trace_context: contextvars.ContextVar[dict[str, Any] | None] = contextvars.ContextVar("trace_context", default=None)


class SpanStatus(Enum):
    """Status of a tracing span."""

    OK = "ok"
    ERROR = "error"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"


class TraceLevel(Enum):
    """Trace level for different types of operations."""

    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class SpanType(Enum):
    """Type of operation being traced."""

    HTTP_REQUEST = "http_request"
    DATABASE_QUERY = "database_query"
    LLM_CALL = "llm_call"
    MEMORY_OPERATION = "memory_operation"
    PIPELINE_STEP = "pipeline_step"
    TOOL_EXECUTION = "tool_execution"
    CACHE_OPERATION = "cache_operation"
    CUSTOM = "custom"


@dataclass
class SpanContext:
    """Context information for a tracing span."""

    trace_id: str
    span_id: str
    parent_span_id: str | None = None
    operation_name: str = ""
    span_type: SpanType = SpanType.CUSTOM
    tags: dict[str, Any] = field(default_factory=dict)
    baggage: dict[str, str] = field(default_factory=dict)


@dataclass
class PerformanceMetrics:
    """Performance metrics collected during span execution."""

    # Timing metrics
    start_time: float = 0.0
    end_time: float = 0.0
    duration: float = 0.0

    # CPU metrics
    cpu_percent_start: float = 0.0
    cpu_percent_end: float = 0.0
    cpu_percent_avg: float = 0.0

    # Memory metrics
    memory_rss_start: float = 0.0  # Resident Set Size in MB
    memory_vms_start: float = 0.0  # Virtual Memory Size in MB
    memory_rss_end: float = 0.0
    memory_vms_end: float = 0.0
    memory_rss_delta: float = 0.0
    memory_vms_delta: float = 0.0

    # I/O metrics
    io_read_count_start: int = 0
    io_write_count_start: int = 0
    io_read_bytes_start: int = 0
    io_write_bytes_start: int = 0
    io_read_count_end: int = 0
    io_write_count_end: int = 0
    io_read_bytes_end: int = 0
    io_write_bytes_end: int = 0
    io_read_delta: int = 0
    io_write_delta: int = 0
    io_read_bytes_delta: int = 0
    io_write_bytes_delta: int = 0

    # Network metrics
    network_sent_start: int = 0
    network_recv_start: int = 0
    network_sent_end: int = 0
    network_recv_end: int = 0
    network_sent_delta: int = 0
    network_recv_delta: int = 0

    # Custom metrics
    custom_metrics: dict[str, float] = field(default_factory=dict)

    def calculate_deltas(self) -> None:
        """Calculate delta values for metrics."""
        self.duration = self.end_time - self.start_time
        self.cpu_percent_avg = (self.cpu_percent_start + self.cpu_percent_end) / 2.0
        self.memory_rss_delta = self.memory_rss_end - self.memory_rss_start
        self.memory_vms_delta = self.memory_vms_end - self.memory_vms_start
        self.io_read_delta = self.io_read_count_end - self.io_read_count_start
        self.io_write_delta = self.io_write_count_end - self.io_write_count_start
        self.io_read_bytes_delta = self.io_read_bytes_end - self.io_read_bytes_start
        self.io_write_bytes_delta = self.io_write_bytes_end - self.io_write_bytes_start
        self.network_sent_delta = self.network_sent_end - self.network_sent_start
        self.network_recv_delta = self.network_recv_end - self.network_recv_start


@dataclass
class SpanData:
    """Complete span data including context and metrics."""

    context: SpanContext
    status: SpanStatus = SpanStatus.OK
    error_message: str | None = None
    error_type: str | None = None
    metrics: PerformanceMetrics = field(default_factory=PerformanceMetrics)
    logs: list[dict[str, Any]] = field(default_factory=list)
    events: list[dict[str, Any]] = field(default_factory=list)

    def add_log(self, level: TraceLevel, message: str, **kwargs: Any) -> None:
        """Add a log entry to the span."""
        self.logs.append(
            {
                "timestamp": time.time(),
                "level": level.value,
                "message": message,
                **kwargs,
            }
        )

    def add_event(self, event_name: str, **kwargs: Any) -> None:
        """Add an event to the span."""
        self.events.append(
            {
                "timestamp": time.time(),
                "event_name": event_name,
                **kwargs,
            }
        )


@dataclass
class TracingConfig:
    """Configuration for distributed tracing."""

    # Sampling configuration
    sampling_rate: float = 1.0  # 0.0 to 1.0
    max_spans_per_second: int = 1000

    # Performance profiling
    enable_performance_profiling: bool = True
    profile_cpu: bool = True
    profile_memory: bool = True
    profile_io: bool = True
    profile_network: bool = True

    # Span configuration
    max_span_duration: float = 300.0  # 5 minutes
    max_logs_per_span: int = 1000
    max_events_per_span: int = 1000

    # Export configuration
    export_to_jaeger: bool = False
    export_to_zipkin: bool = False
    export_to_console: bool = True
    export_to_file: bool = False
    export_file_path: str = "traces.json"

    # Filtering
    exclude_span_types: set[SpanType] = field(default_factory=set)
    min_duration_threshold: float = 0.001  # 1ms

    # Performance tracking
    enable_metrics: bool = True
    log_spans: bool = False


class DistributedTracer:
    """
    Distributed tracer with performance profiling capabilities.

    Provides comprehensive tracing for async operations with detailed
    performance metrics and integration with external tracing systems.
    """

    def __init__(self, config: TracingConfig | None = None):
        """Initialize distributed tracer."""
        self.config = config or TracingConfig()
        self.active_spans: dict[str, SpanData] = {}
        self.completed_spans: list[SpanData] = []

        # Performance tracking
        self.total_spans_created: int = 0
        self.total_spans_completed: int = 0
        self.total_trace_time: float = 0.0

        logger.info(f"Distributed tracer initialized with config: {self.config}")

    def _should_sample(self) -> bool:
        """Determine if the current operation should be sampled."""
        import random

        return random.random() < self.config.sampling_rate

    def _generate_trace_id(self) -> str:
        """Generate a unique trace ID."""
        return str(uuid.uuid4())

    def _generate_span_id(self) -> str:
        """Generate a unique span ID."""
        return str(uuid.uuid4())

    def _get_current_span_id(self) -> str | None:
        """Get the current active span ID from context."""
        trace_context = _trace_context.get()
        if trace_context:
            return trace_context.get("span_id")
        return None

    def _get_process_metrics(self) -> dict[str, Any]:
        """Get current process metrics."""
        process = psutil.Process()
        io_counters = process.io_counters()
        network_counters = psutil.net_io_counters()

        return {
            "cpu_percent": process.cpu_percent(),
            "memory_rss": process.memory_info().rss / 1024 / 1024,  # MB
            "memory_vms": process.memory_info().vms / 1024 / 1024,  # MB
            "io_read_count": io_counters.read_count,
            "io_write_count": io_counters.write_count,
            "io_read_bytes": io_counters.read_bytes,
            "io_write_bytes": io_counters.write_bytes,
            "network_sent": network_counters.bytes_sent,
            "network_recv": network_counters.bytes_recv,
        }

    def _start_performance_profiling(self) -> PerformanceMetrics:
        """Start performance profiling for a span."""
        metrics = PerformanceMetrics()
        metrics.start_time = time.time()

        if self.config.enable_performance_profiling:
            process_metrics = self._get_process_metrics()

            if self.config.profile_cpu:
                metrics.cpu_percent_start = process_metrics["cpu_percent"]

            if self.config.profile_memory:
                metrics.memory_rss_start = process_metrics["memory_rss"]
                metrics.memory_vms_start = process_metrics["memory_vms"]

            if self.config.profile_io:
                metrics.io_read_count_start = process_metrics["io_read_count"]
                metrics.io_write_count_start = process_metrics["io_write_count"]
                metrics.io_read_bytes_start = process_metrics["io_read_bytes"]
                metrics.io_write_bytes_start = process_metrics["io_write_bytes"]

            if self.config.profile_network:
                metrics.network_sent_start = process_metrics["network_sent"]
                metrics.network_recv_start = process_metrics["network_recv"]

        return metrics

    def _end_performance_profiling(self, metrics: PerformanceMetrics) -> None:
        """End performance profiling for a span."""
        metrics.end_time = time.time()

        if self.config.enable_performance_profiling:
            process_metrics = self._get_process_metrics()

            if self.config.profile_cpu:
                metrics.cpu_percent_end = process_metrics["cpu_percent"]

            if self.config.profile_memory:
                metrics.memory_rss_end = process_metrics["memory_rss"]
                metrics.memory_vms_end = process_metrics["memory_vms"]

            if self.config.profile_io:
                metrics.io_read_count_end = process_metrics["io_read_count"]
                metrics.io_write_count_end = process_metrics["io_write_count"]
                metrics.io_read_bytes_end = process_metrics["io_read_bytes"]
                metrics.io_write_bytes_end = process_metrics["io_write_bytes"]

            if self.config.profile_network:
                metrics.network_sent_end = process_metrics["network_sent"]
                metrics.network_recv_end = process_metrics["network_recv"]

        metrics.calculate_deltas()

    def start_span(
        self,
        operation_name: str,
        span_type: SpanType = SpanType.CUSTOM,
        tags: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> SpanContext:
        """Start a new tracing span."""
        if not self._should_sample():
            # Return a no-op context
            return SpanContext(
                trace_id="no-op",
                span_id="no-op",
                operation_name=operation_name,
                span_type=span_type,
            )

        if span_type in self.config.exclude_span_types:
            return SpanContext(
                trace_id="excluded",
                span_id="excluded",
                operation_name=operation_name,
                span_type=span_type,
            )

        # Generate IDs
        trace_id = self._generate_trace_id()
        span_id = self._generate_span_id()
        parent_span_id = self._get_current_span_id()

        # Create span context
        context = SpanContext(
            trace_id=trace_id,
            span_id=span_id,
            parent_span_id=parent_span_id,
            operation_name=operation_name,
            span_type=span_type,
            tags=tags or {},
            **kwargs,
        )

        # Create span data
        span_data = SpanData(context=context)
        span_data.metrics = self._start_performance_profiling()

        # Store active span
        self.active_spans[span_id] = span_data
        self.total_spans_created += 1

        # Set trace context
        trace_context = {
            "trace_id": trace_id,
            "span_id": span_id,
            "parent_span_id": parent_span_id,
        }
        _trace_context.set(trace_context)

        if self.config.log_spans:
            logger.debug(f"Started span {operation_name} ({span_id})")

        return context

    def end_span(
        self,
        span_context: SpanContext,
        status: SpanStatus = SpanStatus.OK,
        error_message: str | None = None,
        error_type: str | None = None,
    ) -> None:
        """End a tracing span."""
        if span_context.span_id in ["no-op", "excluded"]:
            return

        if span_context.span_id not in self.active_spans:
            logger.warning(f"Attempted to end non-existent span: {span_context.span_id}")
            return

        span_data = self.active_spans[span_context.span_id]

        # Update span data
        span_data.status = status
        span_data.error_message = error_message
        span_data.error_type = error_type

        # End performance profiling
        self._end_performance_profiling(span_data.metrics)

        # Check duration threshold
        if span_data.metrics.duration < self.config.min_duration_threshold:
            # Remove from active spans without storing
            del self.active_spans[span_context.span_id]
            return

        # Move to completed spans
        self.completed_spans.append(span_data)
        del self.active_spans[span_context.span_id]
        self.total_spans_completed += 1

        # Update total trace time
        self.total_trace_time += span_data.metrics.duration

        # Export span if configured
        self._export_span(span_data)

        if self.config.log_spans:
            logger.debug(
                f"Ended span {span_context.operation_name} ({span_context.span_id}) "
                f"with status {status.value} in {span_data.metrics.duration:.3f}s"
            )

    def add_span_log(
        self,
        span_context: SpanContext,
        level: TraceLevel,
        message: str,
        **kwargs: Any,
    ) -> None:
        """Add a log entry to a span."""
        if span_context.span_id in ["no-op", "excluded"]:
            return

        if span_context.span_id not in self.active_spans:
            logger.warning(f"Attempted to add log to non-existent span: {span_context.span_id}")
            return

        span_data = self.active_spans[span_context.span_id]

        # Check log limit
        if len(span_data.logs) >= self.config.max_logs_per_span:
            logger.warning(f"Span {span_context.span_id} reached maximum log limit")
            return

        span_data.add_log(level, message, **kwargs)

    def add_span_event(
        self,
        span_context: SpanContext,
        event_name: str,
        **kwargs: Any,
    ) -> None:
        """Add an event to a span."""
        if span_context.span_id in ["no-op", "excluded"]:
            return

        if span_context.span_id not in self.active_spans:
            logger.warning(f"Attempted to add event to non-existent span: {span_context.span_id}")
            return

        span_data = self.active_spans[span_context.span_id]

        # Check event limit
        if len(span_data.events) >= self.config.max_events_per_span:
            logger.warning(f"Span {span_context.span_id} reached maximum event limit")
            return

        span_data.add_event(event_name, **kwargs)

    def _export_span(self, span_data: SpanData) -> None:
        """Export span data to configured destinations."""
        if self.config.export_to_console:
            self._export_to_console(span_data)

        if self.config.export_to_file:
            self._export_to_file(span_data)

        if self.config.export_to_jaeger:
            self._export_to_jaeger(span_data)

        if self.config.export_to_zipkin:
            self._export_to_zipkin(span_data)

    def _export_to_console(self, span_data: SpanData) -> None:
        """Export span to console."""
        context = span_data.context
        metrics = span_data.metrics

        logger.info(f"[TRACE] {context.operation_name} ({context.span_id})")
        logger.info(f"  Duration: {metrics.duration:.3f}s")
        logger.info(f"  Status: {span_data.status.value}")
        if span_data.error_message:
            logger.error(f"  Error: {span_data.error_message}")

        if self.config.enable_performance_profiling:
            logger.info(f"  CPU: {metrics.cpu_percent_avg:.1f}%")
            logger.info(f"  Memory: {metrics.memory_rss_delta:+.1f}MB")
            logger.info(f"  I/O: {metrics.io_read_bytes_delta:,}B read, {metrics.io_write_bytes_delta:,}B written")

    def _export_to_file(self, span_data: SpanData) -> None:
        """Export span to file."""
        # This would implement file export in production

    def _export_to_jaeger(self, span_data: SpanData) -> None:
        """Export span to Jaeger."""
        # This would implement Jaeger export in production

    def _export_to_zipkin(self, span_data: SpanData) -> None:
        """Export span to Zipkin."""
        # This would implement Zipkin export in production

    @contextmanager
    def trace_sync(
        self,
        operation_name: str,
        span_type: SpanType = SpanType.CUSTOM,
        tags: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> Generator[SpanContext, None, None]:
        """Context manager for synchronous tracing."""
        span_context = self.start_span(operation_name, span_type, tags, **kwargs)

        try:
            yield span_context
            self.end_span(span_context, SpanStatus.OK)
        except Exception as e:
            self.end_span(
                span_context,
                SpanStatus.ERROR,
                error_message=str(e),
                error_type=type(e).__name__,
            )
            raise

    @asynccontextmanager
    async def trace_async(
        self,
        operation_name: str,
        span_type: SpanType = SpanType.CUSTOM,
        tags: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> AsyncGenerator[SpanContext, None]:
        """Async context manager for asynchronous tracing."""
        span_context = self.start_span(operation_name, span_type, tags, **kwargs)

        try:
            yield span_context
            self.end_span(span_context, SpanStatus.OK)
        except Exception as e:
            self.end_span(
                span_context,
                SpanStatus.ERROR,
                error_message=str(e),
                error_type=type(e).__name__,
            )
            raise

    def get_trace_metrics(self) -> dict[str, Any]:
        """Get tracing system metrics."""
        active_span_count = len(self.active_spans)
        completed_span_count = len(self.completed_spans)

        avg_span_duration = 0.0
        if completed_span_count > 0:
            total_duration = sum(span.metrics.duration for span in self.completed_spans)
            avg_span_duration = total_duration / completed_span_count

        return {
            "total_spans_created": self.total_spans_created,
            "total_spans_completed": self.total_spans_completed,
            "active_spans": active_span_count,
            "completed_spans": completed_span_count,
            "average_span_duration": avg_span_duration,
            "total_trace_time": self.total_trace_time,
            "sampling_rate": self.config.sampling_rate,
            "performance_profiling_enabled": self.config.enable_performance_profiling,
        }

    def get_span_statistics(self) -> dict[str, Any]:
        """Get detailed span statistics."""
        if not self.completed_spans:
            return {}

        # Group by span type
        spans_by_type: dict[str, list[SpanData]] = {}
        for span in self.completed_spans:
            span_type = span.context.span_type.value
            if span_type not in spans_by_type:
                spans_by_type[span_type] = []
            spans_by_type[span_type].append(span)

        # Calculate statistics
        statistics = {}
        for span_type, spans in spans_by_type.items():
            durations = [span.metrics.duration for span in spans]
            error_count = sum(1 for span in spans if span.status != SpanStatus.OK)

            statistics[span_type] = {
                "count": len(spans),
                "average_duration": sum(durations) / len(durations),
                "min_duration": min(durations),
                "max_duration": max(durations),
                "error_count": error_count,
                "error_rate": error_count / len(spans),
                "total_duration": sum(durations),
            }

        return statistics

    def clear_completed_spans(self) -> None:
        """Clear completed spans to free memory."""
        self.completed_spans.clear()
        logger.info("Cleared completed spans")

    def get_current_span_context(self) -> SpanContext | None:
        """Get the current span context."""
        trace_context = _trace_context.get()
        if trace_context and trace_context.get("span_id") != "no-op":
            return SpanContext(
                trace_id=trace_context.get("trace_id", ""),
                span_id=trace_context.get("span_id", ""),
                parent_span_id=trace_context.get("parent_span_id"),
            )
        return None


# Global tracer instance
_global_tracer: DistributedTracer | None = None


def get_global_tracer() -> DistributedTracer:
    """Get the global tracer instance."""
    global _global_tracer
    if _global_tracer is None:
        _global_tracer = DistributedTracer()
    return _global_tracer


def set_global_tracer(tracer: DistributedTracer) -> None:
    """Set the global tracer instance."""
    global _global_tracer
    _global_tracer = tracer


# Convenience functions for global tracer
def start_span(
    operation_name: str,
    span_type: SpanType = SpanType.CUSTOM,
    tags: dict[str, Any] | None = None,
    **kwargs: Any,
) -> SpanContext:
    """Start a span using the global tracer."""
    return get_global_tracer().start_span(operation_name, span_type, tags, **kwargs)


def end_span(
    span_context: SpanContext,
    status: SpanStatus = SpanStatus.OK,
    error_message: str | None = None,
    error_type: str | None = None,
) -> None:
    """End a span using the global tracer."""
    get_global_tracer().end_span(span_context, status, error_message, error_type)


def add_span_log(
    span_context: SpanContext,
    level: TraceLevel,
    message: str,
    **kwargs: Any,
) -> None:
    """Add a log to a span using the global tracer."""
    get_global_tracer().add_span_log(span_context, level, message, **kwargs)


def add_span_event(
    span_context: SpanContext,
    event_name: str,
    **kwargs: Any,
) -> None:
    """Add an event to a span using the global tracer."""
    get_global_tracer().add_span_event(span_context, event_name, **kwargs)


@contextmanager
def trace_sync(
    operation_name: str,
    span_type: SpanType = SpanType.CUSTOM,
    tags: dict[str, Any] | None = None,
    **kwargs: Any,
) -> Generator[SpanContext, None, None]:
    """Context manager for synchronous tracing using the global tracer."""
    with get_global_tracer().trace_sync(operation_name, span_type, tags, **kwargs) as span_context:
        yield span_context


@asynccontextmanager
async def trace_async(
    operation_name: str,
    span_type: SpanType = SpanType.CUSTOM,
    tags: dict[str, Any] | None = None,
    **kwargs: Any,
) -> AsyncGenerator[SpanContext, None]:
    """Async context manager for asynchronous tracing using the global tracer."""
    async with get_global_tracer().trace_async(operation_name, span_type, tags, **kwargs) as span_context:
        yield span_context
