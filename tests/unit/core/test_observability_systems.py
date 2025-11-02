"""
Comprehensive test suite for observability systems.

Tests distributed tracing, performance profiling, and metrics collection
with various scenarios and edge cases.
"""
import asyncio
import time
import pytest
from platform.core.observability import AggregationType, DistributedTracer, MetricsCollector, MetricsCollectorConfig, MetricType, PerformanceProfiler, ProfilerConfig, ProfilerMode, SpanStatus, SpanType, TraceLevel, TracingConfig

@pytest.fixture(autouse=True)
def reset_observability_systems() -> None:
    """Reset observability systems before each test."""

class TestDistributedTracer:
    """Test distributed tracing functionality."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.config = TracingConfig(sampling_rate=1.0, enable_performance_profiling=True, export_to_console=False, log_spans=False)
        self.tracer = DistributedTracer(self.config)

    def test_tracer_initialization(self) -> None:
        """Test tracer initialization."""
        assert self.tracer.config == self.config
        assert not self.tracer.active_spans
        assert not self.tracer.completed_spans

    def test_start_span(self) -> None:
        """Test starting a span."""
        span_context = self.tracer.start_span('test_operation', SpanType.CUSTOM)
        assert span_context.operation_name == 'test_operation'
        assert span_context.span_type == SpanType.CUSTOM
        assert span_context.span_id in self.tracer.active_spans
        assert self.tracer.active_spans[span_context.span_id].context == span_context

    def test_end_span_success(self) -> None:
        """Test ending a span successfully."""
        span_context = self.tracer.start_span('test_operation')
        time.sleep(0.01)
        self.tracer.end_span(span_context, SpanStatus.OK)
        assert span_context.span_id not in self.tracer.active_spans
        assert len(self.tracer.completed_spans) == 1
        assert self.tracer.completed_spans[0].context == span_context
        assert self.tracer.completed_spans[0].status == SpanStatus.OK

    def test_end_span_with_error(self) -> None:
        """Test ending a span with an error."""
        span_context = self.tracer.start_span('test_operation')
        error_message = 'Test error'
        self.tracer.end_span(span_context, SpanStatus.ERROR, error_message, 'ValueError')
        assert span_context.span_id not in self.tracer.active_spans
        assert len(self.tracer.completed_spans) == 1
        completed_span = self.tracer.completed_spans[0]
        assert completed_span.status == SpanStatus.ERROR
        assert completed_span.error_message == error_message
        assert completed_span.error_type == 'ValueError'

    def test_add_span_log(self) -> None:
        """Test adding logs to a span."""
        span_context = self.tracer.start_span('test_operation')
        self.tracer.add_span_log(span_context, TraceLevel.INFO, 'Test log message', extra_data='test')
        span_data = self.tracer.active_spans[span_context.span_id]
        assert len(span_data.logs) == 1
        assert span_data.logs[0]['message'] == 'Test log message'
        assert span_data.logs[0]['level'] == TraceLevel.INFO.value
        assert span_data.logs[0]['extra_data'] == 'test'

    def test_add_span_event(self) -> None:
        """Test adding events to a span."""
        span_context = self.tracer.start_span('test_operation')
        self.tracer.add_span_event(span_context, 'test_event', event_data='test')
        span_data = self.tracer.active_spans[span_context.span_id]
        assert len(span_data.events) == 1
        assert span_data.events[0]['event_name'] == 'test_event'
        assert span_data.events[0]['event_data'] == 'test'

    def test_trace_sync_context_manager(self) -> None:
        """Test synchronous trace context manager."""
        with self.tracer.trace_sync('sync_operation') as span_context:
            assert span_context.operation_name == 'sync_operation'
            time.sleep(0.01)
        assert span_context.span_id not in self.tracer.active_spans
        assert len(self.tracer.completed_spans) == 1

    def test_trace_sync_context_manager_with_exception(self) -> None:
        """Test synchronous trace context manager with exception."""
        span_context = None
        with pytest.raises(ValueError), self.tracer.trace_sync('sync_operation') as span_context:
            raise ValueError('Test exception')
        assert span_context is not None
        assert span_context.span_id not in self.tracer.active_spans
        assert len(self.tracer.completed_spans) == 1
        assert self.tracer.completed_spans[0].status == SpanStatus.ERROR

    @pytest.mark.asyncio
    async def test_trace_async_context_manager(self) -> None:
        """Test asynchronous trace context manager."""
        async with self.tracer.trace_async('async_operation') as span_context:
            assert span_context.operation_name == 'async_operation'
            await asyncio.sleep(0.01)
        assert span_context.span_id not in self.tracer.active_spans
        assert len(self.tracer.completed_spans) == 1

    @pytest.mark.asyncio
    async def test_trace_async_context_manager_with_exception(self) -> None:
        """Test asynchronous trace context manager with exception."""
        span_context = None
        with pytest.raises(ValueError):
            async with self.tracer.trace_async('async_operation') as span_context:
                raise ValueError('Test exception')
        assert span_context is not None
        assert span_context.span_id not in self.tracer.active_spans
        assert len(self.tracer.completed_spans) == 1
        assert self.tracer.completed_spans[0].status == SpanStatus.ERROR

    def test_sampling_rate_zero(self) -> None:
        """Test tracer with zero sampling rate."""
        self.tracer.config.sampling_rate = 0.0
        span_context = self.tracer.start_span('test_operation')
        assert span_context.span_id == 'no-op'
        assert span_context.trace_id == 'no-op'

    def test_excluded_span_type(self) -> None:
        """Test excluded span types."""
        self.tracer.config.exclude_span_types = {SpanType.CUSTOM}
        span_context = self.tracer.start_span('test_operation', SpanType.CUSTOM)
        assert span_context.span_id == 'excluded'
        assert span_context.trace_id == 'excluded'

    def test_trace_metrics(self) -> None:
        """Test trace metrics collection."""
        for i in range(3):
            span_context = self.tracer.start_span(f'operation_{i}')
            time.sleep(0.01)
            self.tracer.end_span(span_context)
        metrics = self.tracer.get_trace_metrics()
        assert metrics['total_spans_created'] == 3
        assert metrics['total_spans_completed'] == 3
        assert metrics['active_spans'] == 0
        assert metrics['completed_spans'] == 3
        assert metrics['average_span_duration'] > 0

    def test_span_statistics(self) -> None:
        """Test span statistics calculation."""
        for span_type in [SpanType.HTTP_REQUEST, SpanType.DATABASE_QUERY]:
            span_context = self.tracer.start_span('test_operation', span_type)
            time.sleep(0.01)
            self.tracer.end_span(span_context)
        statistics = self.tracer.get_span_statistics()
        assert 'http_request' in statistics
        assert 'database_query' in statistics
        assert statistics['http_request']['count'] == 1
        assert statistics['database_query']['count'] == 1

class TestPerformanceProfiler:
    """Test performance profiling functionality."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.config = ProfilerConfig(enable_function_profiling=True, enable_memory_profiling=True, enable_cpu_profiling=True, profiler_mode=ProfilerMode.TRACE, sample_rate=1.0)
        self.profiler = PerformanceProfiler(self.config)

    def test_profiler_initialization(self) -> None:
        """Test profiler initialization."""
        assert self.profiler.config == self.config
        assert not self.profiler.profile_entries
        assert not self.profiler.function_stats
        assert not self.profiler.is_profiling

    def test_start_stop_profiling(self) -> None:
        """Test starting and stopping profiling."""
        assert not self.profiler.is_profiling
        self.profiler.start_profiling()
        assert self.profiler.is_profiling
        self.profiler.stop_profiling()
        assert not self.profiler.is_profiling

    def test_profile_function_decorator(self) -> None:
        """Test function profiling decorator."""
        self.profiler.start_profiling()

        @self.profiler.profile_function(name='test_function')
        def test_function() -> str:
            time.sleep(0.01)
            return 'result'
        result = test_function()
        assert result == 'result'
        self.profiler.stop_profiling()
        assert len(self.profiler.profile_entries) == 1
        entry = self.profiler.profile_entries[0]
        assert entry.function_name == 'test_function'
        assert entry.duration > 0

    def test_profile_function_decorator_async(self) -> None:
        """Test async function profiling decorator."""
        self.profiler.start_profiling()

        @self.profiler.profile_function(name='test_async_function')
        async def test_async_function() -> str:
            await asyncio.sleep(0.01)
            return 'async_result'

        async def run_test() -> None:
            result = await test_async_function()
            assert result == 'async_result'
        asyncio.run(run_test())
        self.profiler.stop_profiling()
        assert len(self.profiler.profile_entries) == 1
        entry = self.profiler.profile_entries[0]
        assert entry.function_name == 'test_async_function'
        assert entry.is_async
        assert entry.duration > 0

    def test_profile_block_context_manager(self) -> None:
        """Test profile block context manager."""
        self.profiler.start_profiling()
        with self.profiler.profile_block('test_block') as entry:
            assert entry.function_name == 'test_block'
            time.sleep(0.01)
        self.profiler.stop_profiling()
        assert len(self.profiler.profile_entries) == 1
        entry = self.profiler.profile_entries[0]
        assert entry.function_name == 'test_block'
        assert entry.duration > 0

    @pytest.mark.asyncio
    async def test_profile_async_block_context_manager(self) -> None:
        """Test profile async block context manager."""
        self.profiler.start_profiling()
        async with self.profiler.profile_async_block('test_async_block') as entry:
            assert entry.function_name == 'test_async_block'
            assert entry.is_async
            await asyncio.sleep(0.01)
        self.profiler.stop_profiling()
        assert len(self.profiler.profile_entries) == 1
        entry = self.profiler.profile_entries[0]
        assert entry.function_name == 'test_async_block'
        assert entry.is_async
        assert entry.duration > 0

    def test_profile_summary(self) -> None:
        """Test profile summary generation."""
        self.profiler.start_profiling()
        for i in range(3):
            with self.profiler.profile_block(f'test_block_{i}'):
                time.sleep(0.01)
        self.profiler.stop_profiling()
        summary = self.profiler.get_profile_summary()
        assert summary['total_functions_profiled'] == 3
        assert summary['total_profile_entries'] == 3
        assert len(summary['top_functions']) == 3

    def test_detailed_profile_report(self) -> None:
        """Test detailed profile report generation."""
        self.profiler.start_profiling()
        with self.profiler.profile_block('test_block'):
            time.sleep(0.01)
        self.profiler.stop_profiling()
        report = self.profiler.get_detailed_profile_report()
        assert 'PERFORMANCE PROFILE REPORT' in report
        assert 'test_block' in report
        assert 'Profiling Duration:' in report

    def test_sampling_mode(self) -> None:
        """Test profiler in sampling mode."""
        self.profiler.config.profiler_mode = ProfilerMode.SAMPLE
        self.profiler.config.sample_rate = 0.5
        self.profiler.start_profiling()
        for i in range(10):
            with self.profiler.profile_block(f'test_block_{i}'):
                pass
        self.profiler.stop_profiling()
        assert len(self.profiler.profile_entries) <= 10

    def test_clear_profile_data(self) -> None:
        """Test clearing profile data."""
        self.profiler.start_profiling()
        with self.profiler.profile_block('test_block'):
            time.sleep(0.01)
        self.profiler.stop_profiling()
        assert len(self.profiler.profile_entries) == 1
        self.profiler.clear_profile_data()
        assert not self.profiler.profile_entries
        assert not self.profiler.function_stats

    def test_export_profile_data_json(self) -> None:
        """Test exporting profile data as JSON."""
        self.profiler.start_profiling()
        with self.profiler.profile_block('test_block'):
            time.sleep(0.01)
        self.profiler.stop_profiling()
        json_data = self.profiler.export_profile_data('json')
        assert 'config' in json_data
        assert 'summary' in json_data
        assert 'function_stats' in json_data

    def test_export_profile_data_csv(self) -> None:
        """Test exporting profile data as CSV."""
        self.profiler.start_profiling()
        with self.profiler.profile_block('test_block'):
            time.sleep(0.01)
        self.profiler.stop_profiling()
        csv_data = self.profiler.export_profile_data('csv')
        assert 'function_name' in csv_data
        assert 'total_calls' in csv_data
        assert 'test_block' in csv_data

class TestMetricsCollector:
    """Test metrics collection functionality."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.config = MetricsCollectorConfig(enable_system_metrics=False, enable_auto_export=False)
        self.collector = MetricsCollector(self.config)

    def test_collector_initialization(self) -> None:
        """Test metrics collector initialization."""
        assert self.collector.config == self.config
        assert not self.collector.metrics
        assert not self.collector.system_metrics

    def test_record_counter(self) -> None:
        """Test recording counter metrics."""
        self.collector.record_counter('test_counter', 5.0, {'label': 'value'})
        assert 'test_counter' in self.collector.metrics
        metric_data = self.collector.metrics['test_counter']
        assert metric_data.config.metric_type == MetricType.COUNTER
        assert metric_data.aggregated_value == 5.0
        assert len(metric_data.values) == 1

    def test_record_gauge(self) -> None:
        """Test recording gauge metrics."""
        self.collector.record_gauge('test_gauge', 42.0, {'label': 'value'})
        assert 'test_gauge' in self.collector.metrics
        metric_data = self.collector.metrics['test_gauge']
        assert metric_data.config.metric_type == MetricType.GAUGE
        assert metric_data.aggregated_value == 42.0

    def test_record_histogram(self) -> None:
        """Test recording histogram metrics."""
        self.collector.record_histogram('test_histogram', 10.0)
        assert 'test_histogram' in self.collector.metrics
        metric_data = self.collector.metrics['test_histogram']
        assert metric_data.config.metric_type == MetricType.HISTOGRAM
        assert len(metric_data.values) == 1

    def test_record_timer(self) -> None:
        """Test recording timer metrics."""
        self.collector.record_timer('test_timer', 0.5, {'operation': 'test'})
        assert 'test_timer_duration' in self.collector.metrics
        assert 'test_timer_count' in self.collector.metrics
        duration_metric = self.collector.metrics['test_timer_duration']
        count_metric = self.collector.metrics['test_timer_count']
        assert duration_metric.config.metric_type == MetricType.HISTOGRAM
        assert count_metric.config.metric_type == MetricType.COUNTER
        assert count_metric.aggregated_value == 1.0

    def test_time_function_decorator(self) -> None:
        """Test timing function decorator."""

        @self.collector.time_function('test_function')
        def test_function() -> str:
            time.sleep(0.01)
            return 'result'
        result = test_function()
        assert result == 'result'
        assert 'test_function_duration' in self.collector.metrics
        assert 'test_function_count' in self.collector.metrics

    def test_get_metric_value(self) -> None:
        """Test getting metric values."""
        self.collector.record_counter('test_counter', 10.0)
        self.collector.record_counter('test_counter', 5.0)
        value = self.collector.get_metric_value('test_counter')
        assert value == 15.0

    def test_get_metric_history(self) -> None:
        """Test getting metric history."""
        self.collector.record_gauge('test_gauge', 10.0)
        time.sleep(0.01)
        self.collector.record_gauge('test_gauge', 20.0)
        history = self.collector.get_metric_history('test_gauge', duration=1.0)
        assert len(history) == 2
        assert history[0].value == 10.0
        assert history[1].value == 20.0

    def test_get_all_metrics(self) -> None:
        """Test getting all metrics."""
        self.collector.record_counter('counter1', 1.0)
        self.collector.record_gauge('gauge1', 2.0)
        all_metrics = self.collector.get_all_metrics()
        assert 'counter1' in all_metrics
        assert 'gauge1' in all_metrics
        assert all_metrics['counter1']['current_value'] == 1.0
        assert all_metrics['gauge1']['current_value'] == 2.0

    def test_cleanup_old_metrics(self) -> None:
        """Test cleaning up old metric values."""
        self.collector.create_metric('test_metric', MetricType.GAUGE, retention_period=0.01)
        self.collector.record_gauge('test_metric', 10.0)
        time.sleep(0.02)
        removed_count = self.collector.cleanup_old_metrics()
        assert removed_count >= 0

    def test_create_metric(self) -> None:
        """Test creating custom metrics."""
        config = self.collector.create_metric('custom_metric', MetricType.HISTOGRAM, description='A custom metric', labels={'env': 'test'}, aggregation_type=AggregationType.AVERAGE)
        assert 'custom_metric' in self.collector.metrics
        metric_data = self.collector.metrics['custom_metric']
        assert metric_data.config == config
        assert metric_data.config.description == 'A custom metric'
        assert metric_data.config.aggregation_type == AggregationType.AVERAGE

    def test_metrics_summary(self) -> None:
        """Test metrics summary generation."""
        self.collector.record_counter('test_counter', 1.0)
        summary = self.collector.get_metrics_summary()
        assert summary['uptime_seconds'] >= 0
        assert summary['total_metrics_collected'] == 1
        assert summary['active_metrics'] == 1
        assert 'system_metrics' in summary

    @pytest.mark.asyncio
    async def test_export_metrics(self) -> None:
        """Test metrics export."""
        self.collector.record_counter('test_counter', 1.0)
        export_results = await self.collector.export_metrics()
        assert isinstance(export_results, dict)

class TestObservabilityIntegration:
    """Test integration between observability systems."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.tracer = DistributedTracer(TracingConfig(export_to_console=False, log_spans=False))
        self.profiler = PerformanceProfiler(ProfilerConfig())
        self.collector = MetricsCollector(MetricsCollectorConfig(enable_system_metrics=False))

    def test_tracer_with_metrics(self) -> None:
        """Test integrating tracer with metrics collection."""
        with self.tracer.trace_sync('test_operation') as _span_context:
            self.collector.record_counter('span_operations', 1.0)
            time.sleep(0.01)
        assert len(self.tracer.completed_spans) == 1
        assert self.collector.get_metric_value('span_operations') == 1.0

    def test_profiler_with_metrics(self) -> None:
        """Test integrating profiler with metrics collection."""
        self.profiler.start_profiling()

        @self.profiler.profile_function(name='test_function')
        def test_function() -> None:
            self.collector.record_counter('function_calls', 1.0)
            time.sleep(0.01)
        test_function()
        self.profiler.stop_profiling()
        assert len(self.profiler.profile_entries) == 1
        assert self.collector.get_metric_value('function_calls') == 1.0

    def test_all_systems_integration(self) -> None:
        """Test integration of all observability systems."""
        self.profiler.start_profiling()

        @self.profiler.profile_function(name='integrated_function')
        def integrated_function() -> None:
            with self.tracer.trace_sync('inner_operation') as _span_context:
                self.collector.record_counter('integrated_operations', 1.0)
                time.sleep(0.01)
        integrated_function()
        self.profiler.stop_profiling()
        assert len(self.tracer.completed_spans) == 1
        assert len(self.profiler.profile_entries) == 1
        assert self.collector.get_metric_value('integrated_operations') == 1.0

    def test_observability_overhead(self) -> None:
        """Test that observability systems don't add excessive overhead."""
        start_time = time.time()
        for _ in range(100):
            time.sleep(0.001)
        baseline_time = time.time() - start_time
        self.profiler.start_profiling()
        start_time = time.time()
        for i in range(100):
            with self.tracer.trace_sync(f'operation_{i}'):
                self.collector.record_counter('test_counter', 1.0)
                time.sleep(0.001)
        observability_time = time.time() - start_time
        self.profiler.stop_profiling()
        overhead_ratio = observability_time / baseline_time
        assert overhead_ratio < 2.0, f'Observability overhead too high: {overhead_ratio:.2f}x'