"""
Advanced performance profiler for the Ultimate Discord Intelligence Bot.

Provides detailed performance profiling with call stack analysis, memory profiling,
CPU profiling, and async operation tracking for comprehensive performance monitoring.
"""

import asyncio
import functools
import inspect
import logging
import time
import tracemalloc
from collections.abc import AsyncGenerator, Callable, Generator
from contextlib import asynccontextmanager, contextmanager
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

import psutil

logger = logging.getLogger(__name__)


class ProfilerType(Enum):
    """Types of profilers available."""

    FUNCTION = "function"
    LINE = "line"
    MEMORY = "memory"
    CPU = "cpu"
    ASYNC = "async"
    CUSTOM = "custom"


class ProfilerMode(Enum):
    """Profiler operation modes."""

    TRACE = "trace"  # Detailed tracing
    SAMPLE = "sample"  # Sampling-based profiling
    STATISTICAL = "statistical"  # Statistical profiling


@dataclass
class ProfileEntry:
    """Single entry in a performance profile."""

    # Basic information
    function_name: str
    filename: str
    line_number: int
    entry_time: float
    exit_time: float
    duration: float

    # Call information
    call_count: int = 1
    total_time: float = 0.0
    cumulative_time: float = 0.0

    # Memory information
    memory_peak: float = 0.0  # Peak memory usage in MB
    memory_current: float = 0.0  # Current memory usage in MB
    memory_delta: float = 0.0  # Memory change in MB

    # CPU information
    cpu_percent: float = 0.0
    cpu_user_time: float = 0.0
    cpu_system_time: float = 0.0

    # Async information
    is_async: bool = False
    await_count: int = 0
    async_depth: int = 0

    # Custom metrics
    custom_metrics: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Calculate derived metrics."""
        self.duration = self.exit_time - self.entry_time
        self.total_time = self.duration


@dataclass
class ProfileStats:
    """Statistics for a profiled function or operation."""

    function_name: str
    total_calls: int = 0
    total_time: float = 0.0
    average_time: float = 0.0
    min_time: float = float("inf")
    max_time: float = 0.0

    # Memory statistics
    total_memory_peak: float = 0.0
    average_memory_peak: float = 0.0
    total_memory_delta: float = 0.0
    average_memory_delta: float = 0.0

    # CPU statistics
    total_cpu_time: float = 0.0
    average_cpu_percent: float = 0.0

    # Async statistics
    total_await_count: int = 0
    average_await_count: float = 0.0
    max_async_depth: int = 0

    # Timing percentiles
    p50_time: float = 0.0
    p90_time: float = 0.0
    p95_time: float = 0.0
    p99_time: float = 0.0

    def calculate_stats(self, entries: list[ProfileEntry]) -> None:
        """Calculate statistics from profile entries."""
        if not entries:
            return

        self.total_calls = len(entries)
        self.total_time = sum(entry.total_time for entry in entries)
        self.average_time = self.total_time / self.total_calls

        times = [entry.duration for entry in entries]
        self.min_time = min(times)
        self.max_time = max(times)

        # Calculate percentiles
        sorted_times = sorted(times)
        n = len(sorted_times)
        self.p50_time = sorted_times[int(n * 0.5)]
        self.p90_time = sorted_times[int(n * 0.9)]
        self.p95_time = sorted_times[int(n * 0.95)]
        self.p99_time = sorted_times[int(n * 0.99)]

        # Memory statistics
        memory_peaks = [entry.memory_peak for entry in entries if entry.memory_peak > 0]
        if memory_peaks:
            self.total_memory_peak = sum(memory_peaks)
            self.average_memory_peak = self.total_memory_peak / len(memory_peaks)

        memory_deltas = [entry.memory_delta for entry in entries]
        if memory_deltas:
            self.total_memory_delta = sum(memory_deltas)
            self.average_memory_delta = self.total_memory_delta / len(memory_deltas)

        # CPU statistics
        cpu_times = [entry.cpu_user_time + entry.cpu_system_time for entry in entries]
        if cpu_times:
            self.total_cpu_time = sum(cpu_times)

        cpu_percents = [entry.cpu_percent for entry in entries if entry.cpu_percent > 0]
        if cpu_percents:
            self.average_cpu_percent = sum(cpu_percents) / len(cpu_percents)

        # Async statistics
        await_counts = [entry.await_count for entry in entries if entry.is_async]
        if await_counts:
            self.total_await_count = sum(await_counts)
            self.average_await_count = self.total_await_count / len(await_counts)

        async_depths = [entry.async_depth for entry in entries if entry.is_async]
        if async_depths:
            self.max_async_depth = max(async_depths)


@dataclass
class ProfilerConfig:
    """Configuration for the performance profiler."""

    # Profiling types
    enable_function_profiling: bool = True
    enable_line_profiling: bool = False
    enable_memory_profiling: bool = True
    enable_cpu_profiling: bool = True
    enable_async_profiling: bool = True

    # Profiling modes
    profiler_mode: ProfilerMode = ProfilerMode.SAMPLE
    sample_rate: float = 0.1  # 10% sampling rate

    # Memory profiling
    track_memory_allocations: bool = True
    memory_snapshot_interval: float = 0.1  # seconds
    max_memory_snapshots: int = 1000

    # CPU profiling
    track_cpu_usage: bool = True
    cpu_sampling_interval: float = 0.01  # seconds

    # Call stack tracking
    max_call_depth: int = 100
    track_call_stack: bool = True

    # Performance limits
    max_profile_entries: int = 100000
    max_profile_duration: float = 3600.0  # 1 hour

    # Output configuration
    output_format: str = "table"  # table, json, csv
    include_source_lines: bool = False
    sort_by: str = "cumulative_time"  # cumulative_time, self_time, call_count

    # Performance tracking
    enable_metrics: bool = True
    log_profiling_results: bool = True


class PerformanceProfiler:
    """
    Advanced performance profiler with comprehensive profiling capabilities.

    Provides detailed performance analysis including function timing, memory usage,
    CPU utilization, and async operation tracking.
    """

    def __init__(self, config: ProfilerConfig | None = None):
        """Initialize performance profiler."""
        self.config = config or ProfilerConfig()
        self.profile_entries: list[ProfileEntry] = []
        self.function_stats: dict[str, ProfileStats] = {}

        # Memory profiling
        self.memory_snapshots: list[tuple[float, float]] = []  # (timestamp, memory_mb)
        self.memory_traces: dict[str, list[tuple[float, float]]] = {}

        # CPU profiling
        self.cpu_samples: list[tuple[float, float]] = []  # (timestamp, cpu_percent)

        # Call stack tracking
        self.call_stack: list[ProfileEntry] = []
        self.async_depth = 0

        # Performance tracking
        self.profiling_start_time: float = 0.0
        self.total_profile_time: float = 0.0
        self.is_profiling: bool = False

        logger.info(f"Performance profiler initialized with config: {self.config}")

    def start_profiling(self) -> None:
        """Start performance profiling."""
        if self.is_profiling:
            logger.warning("Profiling already started")
            return

        self.profiling_start_time = time.time()
        self.is_profiling = True

        # Start memory profiling if enabled
        if self.config.enable_memory_profiling and self.config.track_memory_allocations:
            tracemalloc.start()

        logger.info("Performance profiling started")

    def stop_profiling(self) -> None:
        """Stop performance profiling."""
        if not self.is_profiling:
            logger.warning("Profiling not started")
            return

        self.total_profile_time = time.time() - self.profiling_start_time
        self.is_profiling = False

        # Stop memory profiling
        if self.config.enable_memory_profiling and self.config.track_memory_allocations:
            tracemalloc.stop()

        # Calculate function statistics
        self._calculate_function_stats()

        logger.info(f"Performance profiling stopped after {self.total_profile_time:.2f}s")

    def _get_current_memory_usage(self) -> float:
        """Get current memory usage in MB."""
        process = psutil.Process()
        return process.memory_info().rss / 1024 / 1024

    def _get_current_cpu_usage(self) -> float:
        """Get current CPU usage percentage."""
        process = psutil.Process()
        return process.cpu_percent()

    def _get_cpu_times(self) -> tuple[float, float]:
        """Get CPU user and system times."""
        process = psutil.Process()
        cpu_times = process.cpu_times()
        return cpu_times.user, cpu_times.system

    def _sample_should_profile(self) -> bool:
        """Determine if current operation should be profiled based on sampling."""
        if self.config.profiler_mode != ProfilerMode.SAMPLE:
            return True

        import random

        return float(random.random()) < self.config.sample_rate

    def _create_profile_entry(
        self,
        function_name: str,
        filename: str,
        line_number: int,
        is_async: bool = False,
        **kwargs: Any,
    ) -> ProfileEntry:
        """Create a new profile entry."""
        current_time = time.time()

        entry = ProfileEntry(
            function_name=function_name,
            filename=filename,
            line_number=line_number,
            entry_time=current_time,
            exit_time=current_time,  # Will be updated when function exits
            duration=0.0,
            is_async=is_async,
            async_depth=self.async_depth,
            **kwargs,
        )

        # Add memory information if enabled
        if self.config.enable_memory_profiling:
            entry.memory_current = self._get_current_memory_usage()

        # Add CPU information if enabled
        if self.config.enable_cpu_profiling:
            entry.cpu_percent = self._get_current_cpu_usage()
            entry.cpu_user_time, entry.cpu_system_time = self._get_cpu_times()

        return entry

    def _update_profile_entry_on_exit(self, entry: ProfileEntry) -> None:
        """Update profile entry when function exits."""
        current_time = time.time()
        entry.exit_time = current_time
        entry.duration = entry.exit_time - entry.entry_time

        # Update memory information
        if self.config.enable_memory_profiling:
            current_memory = self._get_current_memory_usage()
            entry.memory_peak = max(entry.memory_current, current_memory)
            entry.memory_delta = current_memory - entry.memory_current

        # Update CPU information
        if self.config.enable_cpu_profiling:
            current_cpu_user, current_cpu_system = self._get_cpu_times()
            entry.cpu_user_time = current_cpu_user - entry.cpu_user_time
            entry.cpu_system_time = current_cpu_system - entry.cpu_system_time

    def _calculate_function_stats(self) -> None:
        """Calculate statistics for all profiled functions."""
        self.function_stats.clear()

        # Group entries by function name
        function_entries: dict[str, list[ProfileEntry]] = {}
        for entry in self.profile_entries:
            if entry.function_name not in function_entries:
                function_entries[entry.function_name] = []
            function_entries[entry.function_name].append(entry)

        # Calculate statistics for each function
        for function_name, entries in function_entries.items():
            stats = ProfileStats(function_name=function_name)
            stats.calculate_stats(entries)
            self.function_stats[function_name] = stats

    def profile_function(
        self,
        function: Callable[..., Any] | None = None,
        *,
        name: str | None = None,
        include_args: bool = False,
        include_return_value: bool = False,
    ) -> Callable[..., Any]:
        """Decorator to profile a function."""

        def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
            function_name = name or f"{func.__module__}.{func.__qualname__}"
            filename = func.__code__.co_filename
            is_async = asyncio.iscoroutinefunction(func)

            if is_async:

                @functools.wraps(func)
                async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
                    if not self.is_profiling or not self._sample_should_profile():
                        return await func(*args, **kwargs)

                    # Create profile entry
                    entry = self._create_profile_entry(
                        function_name, filename, func.__code__.co_firstlineno, is_async=True
                    )

                    # Add to call stack
                    if self.config.track_call_stack:
                        self.call_stack.append(entry)

                    try:
                        result = await func(*args, **kwargs)
                        return result
                    finally:
                        # Update and remove from call stack
                        if self.config.track_call_stack and self.call_stack:
                            self.call_stack.pop()

                        # Update entry
                        self._update_profile_entry_on_exit(entry)

                        # Store entry
                        self.profile_entries.append(entry)

                return async_wrapper
            else:

                @functools.wraps(func)
                def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
                    if not self.is_profiling or not self._sample_should_profile():
                        return func(*args, **kwargs)

                    # Create profile entry
                    entry = self._create_profile_entry(
                        function_name, filename, func.__code__.co_firstlineno, is_async=False
                    )

                    # Add to call stack
                    if self.config.track_call_stack:
                        self.call_stack.append(entry)

                    try:
                        result = func(*args, **kwargs)
                        return result
                    finally:
                        # Update and remove from call stack
                        if self.config.track_call_stack and self.call_stack:
                            self.call_stack.pop()

                        # Update entry
                        self._update_profile_entry_on_exit(entry)

                        # Store entry
                        self.profile_entries.append(entry)

                return sync_wrapper

        if function is not None:
            return decorator(function)
        return decorator

    @contextmanager
    def profile_block(
        self,
        name: str,
        **kwargs: Any,
    ) -> Generator[ProfileEntry, None, None]:
        """Context manager for profiling a block of code."""
        if not self.is_profiling or not self._sample_should_profile():
            # Return a dummy entry
            entry = ProfileEntry(
                function_name=name,
                filename="<unknown>",
                line_number=0,
                entry_time=time.time(),
                exit_time=time.time(),
                duration=0.0,
            )
            yield entry
            return

        # Get caller information
        frame = inspect.currentframe()
        if frame and frame.f_back:
            caller_frame = frame.f_back
            filename = caller_frame.f_code.co_filename
            line_number = caller_frame.f_lineno
        else:
            filename = "<unknown>"
            line_number = 0

        # Create profile entry
        entry = self._create_profile_entry(name, filename, line_number, **kwargs)

        # Add to call stack
        if self.config.track_call_stack:
            self.call_stack.append(entry)

        try:
            yield entry
        finally:
            # Update and remove from call stack
            if self.config.track_call_stack and self.call_stack:
                self.call_stack.pop()

            # Update entry
            self._update_profile_entry_on_exit(entry)

            # Store entry
            self.profile_entries.append(entry)

    @asynccontextmanager
    async def profile_async_block(
        self,
        name: str,
        **kwargs: Any,
    ) -> AsyncGenerator[ProfileEntry, None]:
        """Async context manager for profiling a block of async code."""
        if not self.is_profiling or not self._sample_should_profile():
            # Return a dummy entry
            entry = ProfileEntry(
                function_name=name,
                filename="<unknown>",
                line_number=0,
                entry_time=time.time(),
                exit_time=time.time(),
                duration=0.0,
                is_async=True,
            )
            yield entry
            return

        # Get caller information
        frame = inspect.currentframe()
        if frame and frame.f_back:
            caller_frame = frame.f_back
            filename = caller_frame.f_code.co_filename
            line_number = caller_frame.f_lineno
        else:
            filename = "<unknown>"
            line_number = 0

        # Create profile entry
        entry = self._create_profile_entry(name, filename, line_number, is_async=True, **kwargs)

        # Track async depth
        self.async_depth += 1

        # Add to call stack
        if self.config.track_call_stack:
            self.call_stack.append(entry)

        try:
            yield entry
        finally:
            # Update and remove from call stack
            if self.config.track_call_stack and self.call_stack:
                self.call_stack.pop()

            # Update async depth
            self.async_depth = max(0, self.async_depth - 1)

            # Update entry
            self._update_profile_entry_on_exit(entry)

            # Store entry
            self.profile_entries.append(entry)

    def get_profile_summary(self) -> dict[str, Any]:
        """Get a summary of the profiling results."""
        if not self.function_stats:
            return {}

        # Sort functions by total time
        sorted_functions = sorted(
            self.function_stats.items(),
            key=lambda x: x[1].total_time,
            reverse=True,
        )

        # Get top functions
        top_functions = sorted_functions[:10]

        summary = {
            "profiling_duration": self.total_profile_time,
            "total_functions_profiled": len(self.function_stats),
            "total_profile_entries": len(self.profile_entries),
            "top_functions": [
                {
                    "function_name": name,
                    "total_time": stats.total_time,
                    "average_time": stats.average_time,
                    "call_count": stats.total_calls,
                    "memory_peak": stats.average_memory_peak,
                    "cpu_percent": stats.average_cpu_percent,
                }
                for name, stats in top_functions
            ],
            "memory_profiling_enabled": self.config.enable_memory_profiling,
            "cpu_profiling_enabled": self.config.enable_cpu_profiling,
            "async_profiling_enabled": self.config.enable_async_profiling,
        }

        return summary

    def get_detailed_profile_report(self) -> str:
        """Get a detailed profile report as a formatted string."""
        if not self.function_stats:
            return "No profiling data available."

        report_lines = []
        report_lines.append("=" * 80)
        report_lines.append("PERFORMANCE PROFILE REPORT")
        report_lines.append("=" * 80)
        report_lines.append(f"Profiling Duration: {self.total_profile_time:.2f}s")
        report_lines.append(f"Total Functions: {len(self.function_stats)}")
        report_lines.append(f"Total Entries: {len(self.profile_entries)}")
        report_lines.append("")

        # Sort functions by total time
        sorted_functions = sorted(
            self.function_stats.items(),
            key=lambda x: x[1].total_time,
            reverse=True,
        )

        # Header
        report_lines.append(f"{'Function':<50} {'Calls':<8} {'Total':<10} {'Avg':<10} {'Min':<10} {'Max':<10}")
        report_lines.append("-" * 100)

        # Function data
        for function_name, stats in sorted_functions:
            report_lines.append(
                f"{function_name:<50} {stats.total_calls:<8} "
                f"{stats.total_time:<10.4f} {stats.average_time:<10.4f} "
                f"{stats.min_time:<10.4f} {stats.max_time:<10.4f}"
            )

        # Memory and CPU summary if enabled
        if self.config.enable_memory_profiling or self.config.enable_cpu_profiling:
            report_lines.append("")
            report_lines.append("MEMORY AND CPU SUMMARY")
            report_lines.append("-" * 50)

            for function_name, stats in sorted_functions:
                if stats.average_memory_peak > 0 or stats.average_cpu_percent > 0:
                    report_lines.append(
                        f"{function_name:<50} "
                        f"Mem: {stats.average_memory_peak:<8.2f}MB "
                        f"CPU: {stats.average_cpu_percent:<6.2f}%"
                    )

        report_lines.append("")
        report_lines.append("=" * 80)

        return "\n".join(report_lines)

    def clear_profile_data(self) -> None:
        """Clear all profiling data."""
        self.profile_entries.clear()
        self.function_stats.clear()
        self.memory_snapshots.clear()
        self.memory_traces.clear()
        self.cpu_samples.clear()
        self.call_stack.clear()
        self.async_depth = 0

        logger.info("Cleared all profiling data")

    def export_profile_data(self, format_type: str = "json") -> str:
        """Export profiling data in specified format."""
        if format_type == "json":
            import json

            data = {
                "config": {
                    "enable_function_profiling": self.config.enable_function_profiling,
                    "enable_memory_profiling": self.config.enable_memory_profiling,
                    "enable_cpu_profiling": self.config.enable_cpu_profiling,
                    "profiler_mode": self.config.profiler_mode.value,
                },
                "summary": self.get_profile_summary(),
                "function_stats": {
                    name: {
                        "total_calls": stats.total_calls,
                        "total_time": stats.total_time,
                        "average_time": stats.average_time,
                        "min_time": stats.min_time,
                        "max_time": stats.max_time,
                        "average_memory_peak": stats.average_memory_peak,
                        "average_cpu_percent": stats.average_cpu_percent,
                    }
                    for name, stats in self.function_stats.items()
                },
            }
            return json.dumps(data, indent=2)

        elif format_type == "csv":
            import csv
            import io

            output = io.StringIO()
            writer = csv.writer(output)

            # Header
            writer.writerow(
                [
                    "function_name",
                    "total_calls",
                    "total_time",
                    "average_time",
                    "min_time",
                    "max_time",
                    "p50_time",
                    "p90_time",
                    "p95_time",
                    "p99_time",
                    "average_memory_peak",
                    "average_cpu_percent",
                ]
            )

            # Data
            for name, stats in self.function_stats.items():
                writer.writerow(
                    [
                        name,
                        stats.total_calls,
                        stats.total_time,
                        stats.average_time,
                        stats.min_time,
                        stats.max_time,
                        stats.p50_time,
                        stats.p90_time,
                        stats.p95_time,
                        stats.p99_time,
                        stats.average_memory_peak,
                        stats.average_cpu_percent,
                    ]
                )

            return output.getvalue()

        else:
            return self.get_detailed_profile_report()


# Global profiler instance
_global_profiler: PerformanceProfiler | None = None


def get_global_profiler() -> PerformanceProfiler:
    """Get the global profiler instance."""
    global _global_profiler
    if _global_profiler is None:
        _global_profiler = PerformanceProfiler()
    return _global_profiler


def set_global_profiler(profiler: PerformanceProfiler) -> None:
    """Set the global profiler instance."""
    global _global_profiler
    _global_profiler = profiler


# Convenience functions for global profiler
def start_profiling() -> None:
    """Start profiling using the global profiler."""
    get_global_profiler().start_profiling()


def stop_profiling() -> None:
    """Stop profiling using the global profiler."""
    get_global_profiler().stop_profiling()


def profile_function(
    function: Callable[..., Any] | None = None,
    *,
    name: str | None = None,
    **kwargs: Any,
) -> Callable[..., Any]:
    """Profile a function using the global profiler."""
    return get_global_profiler().profile_function(function, name=name, **kwargs)


@contextmanager
def profile_block(name: str, **kwargs: Any) -> Generator[ProfileEntry, None, None]:
    """Profile a block of code using the global profiler."""
    with get_global_profiler().profile_block(name, **kwargs) as entry:
        yield entry


@asynccontextmanager
async def profile_async_block(name: str, **kwargs: Any) -> AsyncGenerator[ProfileEntry, None]:
    """Profile an async block of code using the global profiler."""
    async with get_global_profiler().profile_async_block(name, **kwargs) as entry:
        yield entry
