"""Metrics Decorator for Automatic Tool Instrumentation.

This module provides decorators for automatically collecting metrics
from tool usage without modifying existing tool code.
"""

from __future__ import annotations

import functools
import time
from typing import TYPE_CHECKING, Any

from ultimate_discord_intelligence_bot.obs.metrics_collector import record_tool_usage
from ultimate_discord_intelligence_bot.step_result import StepResult


if TYPE_CHECKING:
    from collections.abc import Callable


def instrument_tool(tool_name: str | None = None):
    """Decorator to automatically instrument tool methods with metrics collection.

    Args:
        tool_name: Optional name for the tool. If not provided, uses the function name.

    Example:
        @instrument_tool("AudioTranscriptionTool")
        def _run(self, audio_file: str) -> StepResult:
            # Tool implementation
            pass
    """

    def decorator(func: Callable[..., StepResult]) -> Callable[..., StepResult]:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> StepResult:
            name = tool_name or func.__name__
            if hasattr(args[0], "__class__"):
                name = f"{args[0].__class__.__name__}.{name}"
            start_time = time.perf_counter()
            try:
                result = func(*args, **kwargs)
                execution_time = time.perf_counter() - start_time
                record_tool_usage(name, execution_time, result)
                return result
            except Exception as e:
                execution_time = time.perf_counter() - start_time
                error_result = StepResult.fail(f"Tool execution failed: {e!s}")
                record_tool_usage(name, execution_time, error_result)
                raise

        return wrapper

    return decorator


def instrument_class_methods(cls):
    """Class decorator to automatically instrument all methods that return StepResult.

    This decorator can be applied to tool classes to automatically instrument
    all methods that return StepResult objects.

    Example:
        @instrument_class_methods
        class AudioTranscriptionTool(BaseTool):
            def _run(self, audio_file: str) -> StepResult:
                # Automatically instrumented
                pass
    """
    for attr_name in dir(cls):
        attr = getattr(cls, attr_name)
        if callable(attr) and (not attr_name.startswith("_")):
            import inspect

            sig = inspect.signature(attr)
            if sig.return_annotation == StepResult or sig.return_annotation == "StepResult":
                setattr(cls, attr_name, instrument_tool()(attr))
    return cls


def track_execution_time(tool_name: str | None = None):
    """Decorator to track execution time without full metrics collection.

    This is a lighter-weight alternative to instrument_tool for cases
    where you only need execution time tracking.

    Args:
        tool_name: Optional name for the tool.
    """

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            name = tool_name or func.__name__
            start_time = time.perf_counter()
            try:
                result = func(*args, **kwargs)
                execution_time = time.perf_counter() - start_time
                print(f"⏱️  {name} executed in {execution_time:.4f}s")
                return result
            except Exception as e:
                execution_time = time.perf_counter() - start_time
                print(f"❌ {name} failed after {execution_time:.4f}s: {e}")
                raise

        return wrapper

    return decorator


def track_memory_usage(tool_name: str | None = None):
    """Decorator to track memory usage during tool execution.

    Args:
        tool_name: Optional name for the tool.
    """

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            name = tool_name or func.__name__
            try:
                import os

                import psutil

                process = psutil.Process(os.getpid())
                memory_before = process.memory_info().rss / 1024 / 1024
                result = func(*args, **kwargs)
                memory_after = process.memory_info().rss / 1024 / 1024
                memory_delta = memory_after - memory_before
                print(f"💾 {name} memory usage: {memory_delta:+.2f} MB (total: {memory_after:.2f} MB)")
                return result
            except ImportError:
                print(f"⚠️  psutil not available for memory tracking in {name}")
                return func(*args, **kwargs)
            except Exception as e:
                print(f"❌ Memory tracking failed for {name}: {e}")
                return func(*args, **kwargs)

        return wrapper

    return decorator


def track_errors(tool_name: str | None = None):
    """Decorator to track and log errors during tool execution.

    Args:
        tool_name: Optional name for the tool.
    """

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            name = tool_name or func.__name__
            try:
                return func(*args, **kwargs)
            except Exception as e:
                print(f"❌ Error in {name}: {type(e).__name__}: {e}")
                raise

        return wrapper

    return decorator


def comprehensive_instrumentation(tool_name: str | None = None):
    """Decorator that combines multiple instrumentation features.

    This decorator provides comprehensive instrumentation including:
    - Execution time tracking
    - Memory usage monitoring
    - Error tracking
    - Metrics collection

    Args:
        tool_name: Optional name for the tool.
    """

    def decorator(func: Callable[..., StepResult]) -> Callable[..., StepResult]:
        instrumented = instrument_tool(tool_name)(func)
        instrumented = track_memory_usage(tool_name)(instrumented)
        instrumented = track_errors(tool_name)(instrumented)
        return instrumented

    return decorator
