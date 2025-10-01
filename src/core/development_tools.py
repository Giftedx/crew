"""Comprehensive development tools for debugging, profiling, and testing.

This module provides advanced debugging capabilities, performance profiling,
and development utilities for the Ultimate Discord Intelligence Bot.
"""

from __future__ import annotations

import asyncio
import json
import logging
import sys
import threading
import time
import traceback
from collections import defaultdict
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class PerformanceProfile:
    """Performance profiling results."""

    operation_name: str
    total_time: float
    call_count: int
    average_time: float
    function_calls: dict[str, dict[str, Any]] = field(default_factory=dict)
    memory_usage: dict[str, float] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)


@dataclass
class DebugSnapshot:
    """Debug snapshot of system state."""

    timestamp: float
    operation_id: str
    operation_type: str
    stack_trace: str
    local_variables: dict[str, Any]
    system_metrics: dict[str, Any]
    memory_info: dict[str, Any]
    thread_info: dict[str, Any]


class PerformanceProfiler:
    """Advanced performance profiler for system optimization."""

    def __init__(self):
        self.profiles: dict[str, PerformanceProfile] = {}
        self.enabled_operations: set[str] = set()
        self.profile_data: dict[str, list[float]] = defaultdict(list)

    def enable_profiling(self, operation_name: str) -> None:
        """Enable profiling for a specific operation."""
        self.enabled_operations.add(operation_name)
        logger.info(f"Performance profiling enabled for: {operation_name}")

    def disable_profiling(self, operation_name: str) -> None:
        """Disable profiling for a specific operation."""
        self.enabled_operations.discard(operation_name)
        logger.info(f"Performance profiling disabled for: {operation_name}")

    @contextmanager
    def profile_operation(self, operation_name: str, operation_id: str | None = None):
        """Context manager for profiling operations."""
        if operation_name not in self.enabled_operations:
            yield
            return

        start_time = time.time()
        start_memory = self._get_memory_usage()

        try:
            yield
        finally:
            end_time = time.time()
            end_memory = self._get_memory_usage()

            duration = end_time - start_time
            memory_delta = end_memory - start_memory

            self._record_profile(operation_name, duration, memory_delta, operation_id or operation_name)

    def _get_memory_usage(self) -> float:
        """Get current memory usage in MB."""
        try:
            import psutil

            process = psutil.Process()
            return process.memory_info().rss / 1024 / 1024  # MB
        except ImportError:
            return 0.0

    def _record_profile(self, operation_name: str, duration: float, memory_delta: float, operation_id: str) -> None:
        """Record profiling data."""
        if operation_name not in self.profiles:
            self.profiles[operation_name] = PerformanceProfile(
                operation_name=operation_name,
                total_time=0.0,
                call_count=0,
                average_time=0.0,
            )

        profile = self.profiles[operation_name]
        profile.total_time += duration
        profile.call_count += 1
        profile.average_time = profile.total_time / profile.call_count
        profile.memory_usage[operation_id] = memory_delta

        # Store timing data for analysis
        self.profile_data[operation_name].append(duration)

    def get_profile_summary(self, operation_name: str | None = None) -> dict[str, Any]:
        """Get performance profile summary."""
        if operation_name:
            if operation_name not in self.profiles:
                return {"error": f"No profile data for: {operation_name}"}

            profile = self.profiles[operation_name]
            timing_data = self.profile_data[operation_name]

            return {
                "operation_name": operation_name,
                "total_calls": profile.call_count,
                "total_time": profile.total_time,
                "average_time": profile.average_time,
                "min_time": min(timing_data) if timing_data else 0.0,
                "max_time": max(timing_data) if timing_data else 0.0,
                "memory_usage": profile.memory_usage,
                "performance_trend": self._calculate_performance_trend(timing_data),
            }
        else:
            # Return summary for all operations
            summaries = {}
            for op_name in self.profiles:
                summaries[op_name] = self.get_profile_summary(op_name)
            return summaries

    def _calculate_performance_trend(self, timing_data: list[float]) -> str:
        """Calculate performance trend from timing data."""
        if len(timing_data) < 5:
            return "insufficient_data"

        recent = timing_data[-5:]
        older = timing_data[:-5] if len(timing_data) > 5 else timing_data

        recent_avg = sum(recent) / len(recent)
        older_avg = sum(older) / len(older)

        if recent_avg < older_avg * 0.9:  # 10% improvement
            return "improving"
        elif recent_avg > older_avg * 1.1:  # 10% degradation
            return "degrading"
        else:
            return "stable"

    def export_profiles(self, format: str = "json") -> str:
        """Export performance profiles."""
        if format == "json":
            return json.dumps(
                {
                    "profiles": {
                        name: {
                            "total_time": profile.total_time,
                            "call_count": profile.call_count,
                            "average_time": profile.average_time,
                            "memory_usage": profile.memory_usage,
                        }
                        for name, profile in self.profiles.items()
                    },
                    "exported_at": time.time(),
                },
                indent=2,
            )
        else:
            return "Unsupported format"


class SystemDebugger:
    """Advanced debugging system for system introspection."""

    def __init__(self):
        self.snapshots: list[DebugSnapshot] = []
        self.max_snapshots = 100
        self.debug_mode = False

    def enable_debug_mode(self) -> None:
        """Enable debug mode for enhanced introspection."""
        self.debug_mode = True
        logger.info("Debug mode enabled")

    def disable_debug_mode(self) -> None:
        """Disable debug mode."""
        self.debug_mode = False
        logger.info("Debug mode disabled")

    def capture_snapshot(self, operation_id: str, operation_type: str, include_locals: bool = True) -> DebugSnapshot:
        """Capture a debug snapshot of current system state."""
        timestamp = time.time()

        # Get stack trace
        stack_trace = traceback.format_stack()

        # Get local variables (if enabled)
        local_variables = {}
        if include_locals:
            try:
                frame = sys._getframe(1)  # Get caller's frame
                local_variables = frame.f_locals.copy()
                # Remove large objects to avoid memory issues
                for key, value in local_variables.items():
                    if hasattr(value, "__sizeof__") and value.__sizeof__() > 10000:
                        local_variables[key] = f"<Large object: {type(value).__name__}>"
            except Exception:
                local_variables = {"error": "Could not capture locals"}

        # Get system metrics
        system_metrics = self._get_system_metrics()

        # Get memory info
        memory_info = self._get_memory_info()

        # Get thread info
        thread_info = self._get_thread_info()

        snapshot = DebugSnapshot(
            timestamp=timestamp,
            operation_id=operation_id,
            operation_type=operation_type,
            stack_trace="".join(stack_trace),
            local_variables=local_variables,
            system_metrics=system_metrics,
            memory_info=memory_info,
            thread_info=thread_info,
        )

        # Store snapshot
        self.snapshots.append(snapshot)
        if len(self.snapshots) > self.max_snapshots:
            self.snapshots = self.snapshots[-self.max_snapshots :]

        return snapshot

    def _get_system_metrics(self) -> dict[str, Any]:
        """Get system performance metrics."""
        metrics_data = {}

        try:
            # CPU usage
            import psutil

            metrics_data["cpu_percent"] = psutil.cpu_percent(interval=0.1)

            # Memory usage
            memory = psutil.virtual_memory()
            metrics_data["memory_percent"] = memory.percent
            metrics_data["memory_available"] = memory.available

            # Disk usage
            disk = psutil.disk_usage("/")
            metrics_data["disk_percent"] = disk.percent
            metrics_data["disk_free"] = disk.free

        except ImportError:
            metrics_data["psutil_unavailable"] = True

        return metrics_data

    def _get_memory_info(self) -> dict[str, Any]:
        """Get detailed memory information."""
        info = {}

        try:
            import psutil

            process = psutil.Process()

            memory_info = process.memory_info()
            info["rss_mb"] = memory_info.rss / 1024 / 1024
            info["vms_mb"] = memory_info.vms / 1024 / 1024

            # Memory maps (simplified)
            try:
                memory_maps = process.memory_maps()
                info["memory_maps_count"] = len(memory_maps)
            except Exception:
                info["memory_maps_count"] = 0

        except ImportError:
            info["psutil_unavailable"] = True

        return info

    def _get_thread_info(self) -> dict[str, Any]:
        """Get thread information."""
        info = {
            "current_thread_id": threading.get_ident(),
            "active_threads": threading.active_count(),
        }

        try:
            import psutil

            process = psutil.Process()
            threads = process.threads()

            info["process_threads"] = len(threads)
            info["thread_states"] = {}

            for thread in threads[:10]:  # Limit to first 10 threads
                thread_id = thread.id
                # This would need more complex logic to map to Python threads
                info["thread_states"][f"thread_{thread_id}"] = {
                    "cpu_time": thread.user_time + thread.system_time,
                    "status": "unknown",  # Would need thread mapping
                }

        except ImportError:
            info["psutil_unavailable"] = True

        return info

    def get_snapshots(
        self, operation_id: str | None = None, operation_type: str | None = None, limit: int = 10
    ) -> list[DebugSnapshot]:
        """Get debug snapshots with optional filtering."""
        snapshots = self.snapshots

        if operation_id:
            snapshots = [s for s in snapshots if s.operation_id == operation_id]

        if operation_type:
            snapshots = [s for s in snapshots if s.operation_type == operation_type]

        # Sort by timestamp (most recent first)
        snapshots.sort(key=lambda s: s.timestamp, reverse=True)

        return snapshots[:limit]

    def export_snapshots(self, format: str = "json") -> str:
        """Export debug snapshots."""
        if format == "json":
            snapshots_data = []
            for snapshot in self.snapshots[-50:]:  # Last 50 snapshots
                snapshots_data.append(
                    {
                        "timestamp": snapshot.timestamp,
                        "operation_id": snapshot.operation_id,
                        "operation_type": snapshot.operation_type,
                        "system_metrics": snapshot.system_metrics,
                        "memory_info": snapshot.memory_info,
                        "thread_info": snapshot.thread_info,
                        "stack_trace_preview": snapshot.stack_trace.split("\n")[-5:],  # Last 5 lines
                    }
                )

            return json.dumps(
                {
                    "snapshots": snapshots_data,
                    "total_snapshots": len(self.snapshots),
                    "exported_at": time.time(),
                },
                indent=2,
            )
        else:
            return "Unsupported format"


class DevelopmentUtilities:
    """Development utilities for testing and rapid iteration."""

    def __init__(self):
        self.profiler = PerformanceProfiler()
        self.debugger = SystemDebugger()
        self.test_scenarios: dict[str, dict[str, Any]] = {}
        self.mock_data: dict[str, Any] = {}

    def register_test_scenario(self, name: str, scenario_data: dict[str, Any]) -> None:
        """Register a test scenario for quick testing."""
        self.test_scenarios[name] = scenario_data
        logger.info(f"Registered test scenario: {name}")

    def run_test_scenario(self, scenario_name: str) -> dict[str, Any]:
        """Run a registered test scenario."""
        if scenario_name not in self.test_scenarios:
            return {"error": f"Test scenario not found: {scenario_name}"}

        scenario = self.test_scenarios[scenario_name]

        # This would execute the scenario
        # For now, just return scenario info
        return {
            "scenario_name": scenario_name,
            "scenario_type": scenario.get("type", "unknown"),
            "expected_outcome": scenario.get("expected_outcome", "unknown"),
            "executed_at": time.time(),
        }

    def create_mock_data(self, data_type: str, **kwargs) -> dict[str, Any]:
        """Create mock data for testing."""
        mock_generators = {
            "youtube_video": self._mock_youtube_video,
            "transcript": self._mock_transcript,
            "analysis_result": self._mock_analysis_result,
            "discord_message": self._mock_discord_message,
        }

        generator = mock_generators.get(data_type)
        if not generator:
            return {"error": f"Unknown mock data type: {data_type}"}

        return generator(**kwargs)

    def _mock_youtube_video(self, **kwargs) -> dict[str, Any]:
        """Create mock YouTube video data."""
        return {
            "id": kwargs.get("video_id", "test_video_123"),
            "title": kwargs.get("title", "Test Video Title"),
            "description": kwargs.get("description", "Test video description"),
            "duration": kwargs.get("duration", 300),
            "uploader": kwargs.get("uploader", "Test Creator"),
            "upload_date": kwargs.get("upload_date", "2023-01-01"),
            "view_count": kwargs.get("view_count", 1000),
            "platform": "youtube",
        }

    def _mock_transcript(self, **kwargs) -> dict[str, Any]:
        """Create mock transcript data."""
        return {
            "text": kwargs.get("text", "This is a test transcript for debugging purposes."),
            "language": kwargs.get("language", "en"),
            "confidence": kwargs.get("confidence", 0.95),
            "segments": [
                {
                    "start": 0.0,
                    "end": 5.0,
                    "text": "This is a test transcript",
                    "confidence": 0.95,
                }
            ],
        }

    def _mock_analysis_result(self, **kwargs) -> dict[str, Any]:
        """Create mock analysis result."""
        return {
            "sentiment": kwargs.get("sentiment", "neutral"),
            "keywords": kwargs.get("keywords", ["test", "analysis"]),
            "summary": kwargs.get("summary", "This is a test analysis summary"),
            "trust_score": kwargs.get("trust_score", 0.8),
            "fact_check_status": kwargs.get("fact_check_status", "verified"),
        }

    def _mock_discord_message(self, **kwargs) -> dict[str, Any]:
        """Create mock Discord message."""
        return {
            "id": kwargs.get("message_id", "123456789"),
            "content": kwargs.get("content", "Test Discord message"),
            "author": kwargs.get("author", "TestUser"),
            "channel_id": kwargs.get("channel_id", "987654321"),
            "timestamp": kwargs.get("timestamp", time.time()),
        }

    def get_system_status(self) -> dict[str, Any]:
        """Get comprehensive system status for debugging."""
        return {
            "timestamp": time.time(),
            "python_version": sys.version,
            "platform": sys.platform,
            "memory_usage": self._get_memory_usage_mb(),
            "active_threads": threading.active_count(),
            "loaded_modules": len(sys.modules),
            "profiler_enabled_operations": list(self.profiler.enabled_operations),
            "debugger_mode": self.debugger.debug_mode,
            "test_scenarios_registered": len(self.test_scenarios),
        }

    def _get_memory_usage_mb(self) -> float:
        """Get current memory usage in MB."""
        try:
            import psutil

            process = psutil.Process()
            return process.memory_info().rss / 1024 / 1024
        except ImportError:
            return 0.0


class InteractiveDebugger:
    """Interactive debugging interface for real-time system inspection."""

    def __init__(self):
        self.debug_session_active = False
        self.breakpoints: dict[str, callable] = {}
        self.debug_hooks: dict[str, list[callable]] = defaultdict(list)

    def start_debug_session(self) -> None:
        """Start an interactive debug session."""
        self.debug_session_active = True
        logger.info("Interactive debug session started")

    def stop_debug_session(self) -> None:
        """Stop the debug session."""
        self.debug_session_active = False
        logger.info("Interactive debug session stopped")

    def add_breakpoint(self, operation_name: str, callback: callable) -> None:
        """Add a breakpoint for a specific operation."""
        self.breakpoints[operation_name] = callback
        logger.info(f"Added breakpoint for: {operation_name}")

    def add_debug_hook(self, hook_name: str, callback: callable) -> None:
        """Add a debug hook for monitoring operations."""
        self.debug_hooks[hook_name].append(callback)
        logger.info(f"Added debug hook: {hook_name}")

    def trigger_breakpoint(self, operation_name: str, context: dict[str, Any]) -> dict[str, Any]:
        """Trigger a breakpoint if registered."""
        if operation_name in self.breakpoints and self.debug_session_active:
            try:
                return self.breakpoints[operation_name](context)
            except Exception as e:
                logger.error(f"Error in breakpoint callback: {e}")
                return {"error": str(e)}

        return {"status": "no_breakpoint"}

    def trigger_debug_hooks(self, hook_name: str, context: dict[str, Any]) -> None:
        """Trigger debug hooks for monitoring."""
        for hook in self.debug_hooks.get(hook_name, []):
            try:
                hook(context)
            except Exception as e:
                logger.error(f"Error in debug hook {hook_name}: {e}")


# Global development tools instances
_profiler: PerformanceProfiler | None = None
_debugger: SystemDebugger | None = None
_dev_utils: DevelopmentUtilities | None = None
_interactive_debugger: InteractiveDebugger | None = None


def get_profiler() -> PerformanceProfiler:
    """Get or create the global performance profiler."""
    global _profiler

    if _profiler is None:
        _profiler = PerformanceProfiler()
    return _profiler


def get_debugger() -> SystemDebugger:
    """Get or create the global system debugger."""
    global _debugger

    if _debugger is None:
        _debugger = SystemDebugger()
    return _debugger


def get_dev_utils() -> DevelopmentUtilities:
    """Get or create the global development utilities."""
    global _dev_utils

    if _dev_utils is None:
        _dev_utils = DevelopmentUtilities()
    return _dev_utils


def get_interactive_debugger() -> InteractiveDebugger:
    """Get or create the global interactive debugger."""
    global _interactive_debugger

    if _interactive_debugger is None:
        _interactive_debugger = InteractiveDebugger()
    return _interactive_debugger


# Convenience functions
def profile_operation(operation_name: str):
    """Decorator for profiling operations."""

    def decorator(func):
        def wrapper(*args, **kwargs):
            profiler = get_profiler()
            with profiler.profile_operation(operation_name, f"{func.__name__}_{id(func)}"):
                return func(*args, **kwargs)

        return wrapper

    return decorator


def debug_snapshot(operation_id: str, operation_type: str):
    """Decorator for capturing debug snapshots."""

    def decorator(func):
        async def async_wrapper(*args, **kwargs):
            debugger = get_debugger()
            debugger.capture_snapshot(operation_id, operation_type, include_locals=True)
            return await func(*args, **kwargs)

        def sync_wrapper(*args, **kwargs):
            debugger = get_debugger()
            debugger.capture_snapshot(operation_id, operation_type, include_locals=True)
            return func(*args, **kwargs)

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


def enable_profiling(operation_name: str) -> None:
    """Enable profiling for an operation."""
    profiler = get_profiler()
    profiler.enable_profiling(operation_name)


def capture_debug_snapshot(operation_id: str, operation_type: str) -> DebugSnapshot:
    """Capture a debug snapshot."""
    debugger = get_debugger()
    return debugger.capture_snapshot(operation_id, operation_type)


def register_test_scenario(name: str, scenario_data: dict[str, Any]) -> None:
    """Register a test scenario."""
    dev_utils = get_dev_utils()
    dev_utils.register_test_scenario(name, scenario_data)


def get_system_status() -> dict[str, Any]:
    """Get comprehensive system status."""
    dev_utils = get_dev_utils()
    return dev_utils.get_system_status()


def initialize_development_tools() -> None:
    """Initialize development tools."""
    logger.info("Initializing development tools...")

    # Initialize all tools
    get_profiler()
    get_debugger()
    get_dev_utils()
    get_interactive_debugger()

    # Enable profiling for key operations
    enable_profiling("pipeline_process_video")
    enable_profiling("llm_request")
    enable_profiling("memory_search")

    logger.info("Development tools initialized")


__all__ = [
    "PerformanceProfiler",
    "SystemDebugger",
    "DevelopmentUtilities",
    "InteractiveDebugger",
    "PerformanceProfile",
    "DebugSnapshot",
    "get_profiler",
    "get_debugger",
    "get_dev_utils",
    "get_interactive_debugger",
    "profile_operation",
    "debug_snapshot",
    "enable_profiling",
    "capture_debug_snapshot",
    "register_test_scenario",
    "get_system_status",
    "initialize_development_tools",
]
