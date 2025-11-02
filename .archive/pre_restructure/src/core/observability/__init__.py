"""
Observability module for the Ultimate Discord Intelligence Bot.

Provides comprehensive observability capabilities including distributed tracing,
performance profiling, and metrics collection for production monitoring.
"""

from src.core.observability.distributed_tracing import (
    DistributedTracer,
    SpanContext,
    SpanData,
    SpanStatus,
    SpanType,
    TraceLevel,
    TracingConfig,
    add_span_event,
    add_span_log,
    end_span,
    get_global_tracer,
    set_global_tracer,
    start_span,
    trace_async,
    trace_sync,
)
from src.core.observability.metrics_collector import (
    AggregationType,
    MetricBackend,
    MetricsCollector,
    MetricsCollectorConfig,
    MetricType,
    get_global_metrics_collector,
    record_counter,
    record_gauge,
    record_histogram,
    record_timer,
    set_global_metrics_collector,
    time_function,
)
from src.core.observability.performance_profiler import (
    PerformanceProfiler,
    ProfilerConfig,
    ProfilerMode,
    ProfilerType,
    get_global_profiler,
    profile_async_block,
    profile_block,
    profile_function,
    set_global_profiler,
    start_profiling,
    stop_profiling,
)


__all__ = [
    # Metrics collection
    "AggregationType",
    # Distributed tracing
    "DistributedTracer",
    "MetricBackend",
    "MetricType",
    "MetricsCollector",
    "MetricsCollectorConfig",
    # Performance profiling
    "PerformanceProfiler",
    "ProfilerConfig",
    "ProfilerMode",
    "ProfilerType",
    "SpanContext",
    "SpanData",
    "SpanStatus",
    "SpanType",
    "TraceLevel",
    "TracingConfig",
    "add_span_event",
    "add_span_log",
    "end_span",
    "get_global_metrics_collector",
    "get_global_profiler",
    "get_global_tracer",
    "profile_async_block",
    "profile_block",
    "profile_function",
    "record_counter",
    "record_gauge",
    "record_histogram",
    "record_timer",
    "set_global_metrics_collector",
    "set_global_profiler",
    "set_global_tracer",
    "start_profiling",
    "start_span",
    "stop_profiling",
    "time_function",
    "trace_async",
    "trace_sync",
]
