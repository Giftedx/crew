"""Agent execution metrics collection.

Provides Prometheus instrumentation for CrewAI agent lifecycle events, enabling
monitoring of agent executions, durations, errors, and resource usage across all
31 specialized agents in the system.

Design:
- Low-cardinality labels: agent name, status (success/fail), error_category
- Metrics: counters (executions, errors), histograms (duration, token usage)
- Thread-safe: safe for concurrent agent execution
- StepResult-aware: integrates with error recovery and observability

Usage:
    from platform.observability.agent_metrics import AgentMetricsCollector

    collector = AgentMetricsCollector.get_instance()

    # Track agent execution
    with collector.track_execution(agent_name="Acquisition Specialist"):
        result = agent.execute(task)

    # Or manually
    collector.record_execution(
        agent_name="Verification Director",
        status="success",
        duration_seconds=2.5,
        tokens_used=1500
    )
"""

from __future__ import annotations

import logging
import time
from contextlib import contextmanager
from platform.core.step_result import ErrorCategory, StepResult
from typing import TYPE_CHECKING, Any


if TYPE_CHECKING:
    from collections.abc import Generator


logger = logging.getLogger(__name__)


try:
    from prometheus_client import Counter, Histogram

    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False
    logger.warning("prometheus_client not available, agent metrics will be no-op")

    # No-op stubs
    class Counter:  # type: ignore[no-redef]
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            pass

        def labels(self, *args: Any, **kwargs: Any) -> Counter:
            return self

        def inc(self, amount: float = 1) -> None:
            pass

    class Histogram:  # type: ignore[no-redef]
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            pass

        def labels(self, *args: Any, **kwargs: Any) -> Histogram:
            return self

        def observe(self, value: float) -> None:
            pass


class AgentMetricsCollector:
    """Singleton collector for agent execution metrics.

    Instruments all agent lifecycle events with Prometheus metrics:
    - agent_executions_total: Counter of agent executions by agent/status
    - agent_execution_duration_seconds: Histogram of execution durations by agent
    - agent_errors_total: Counter of agent errors by agent/category
    - agent_tokens_used_total: Counter of tokens consumed by agent

    Thread-safe for concurrent agent execution.
    """

    _instance: AgentMetricsCollector | None = None

    def __init__(self) -> None:
        """Initialize Prometheus metrics (internal, use get_instance())."""
        if not PROMETHEUS_AVAILABLE:
            logger.debug("Prometheus unavailable, metrics will be no-op")
            self._enabled = False
            return

        self._enabled = True

        # Counter: total agent executions by agent name and status
        self.agent_executions_total = Counter(
            "agent_executions_total",
            "Total number of agent executions",
            ["agent", "status"],
        )

        # Histogram: agent execution duration in seconds by agent name
        self.agent_execution_duration_seconds = Histogram(
            "agent_execution_duration_seconds",
            "Agent execution duration in seconds",
            ["agent"],
            buckets=(0.1, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0, 120.0, 300.0),
        )

        # Counter: agent errors by agent name and error category
        self.agent_errors_total = Counter(
            "agent_errors_total",
            "Total number of agent errors",
            ["agent", "category"],
        )

        # Counter: tokens used by agent (input + output)
        self.agent_tokens_used_total = Counter(
            "agent_tokens_used_total",
            "Total tokens consumed by agent executions",
            ["agent"],
        )

        logger.info("AgentMetricsCollector initialized with Prometheus metrics")

    @classmethod
    def get_instance(cls) -> AgentMetricsCollector:
        """Get singleton instance (lazy initialization)."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def record_execution(
        self,
        agent_name: str,
        status: str,
        duration_seconds: float | None = None,
        error_category: ErrorCategory | None = None,
        tokens_used: int | None = None,
    ) -> None:
        """Record agent execution metrics.

        Args:
            agent_name: Name of the agent (e.g., "Acquisition Specialist")
            status: Execution status ("success", "fail", "skip")
            duration_seconds: Optional execution duration in seconds
            error_category: Optional error category if status="fail"
            tokens_used: Optional token count (input + output)
        """
        if not self._enabled:
            return

        try:
            # Increment execution counter
            self.agent_executions_total.labels(agent=agent_name, status=status).inc()

            # Record duration if provided
            if duration_seconds is not None:
                self.agent_execution_duration_seconds.labels(agent=agent_name).observe(duration_seconds)

            # Record error if failed
            if status == "fail" and error_category is not None:
                category_str = error_category.name if hasattr(error_category, "name") else str(error_category)
                self.agent_errors_total.labels(agent=agent_name, category=category_str).inc()

            # Record token usage if provided
            if tokens_used is not None and tokens_used > 0:
                self.agent_tokens_used_total.labels(agent=agent_name).inc(tokens_used)

        except Exception as exc:
            logger.debug("Failed to record agent metrics: %s", exc)

    @contextmanager
    def track_execution(self, agent_name: str) -> Generator[dict[str, Any], None, None]:
        """Context manager for tracking agent execution.

        Automatically records execution time and status. Caller should update
        the context dict with error_category and tokens_used as needed.

        Args:
            agent_name: Name of the agent being executed

        Yields:
            Context dict for caller to populate (error_category, tokens_used)

        Example:
            with collector.track_execution("Verification Director") as ctx:
                result = agent.execute(task)
                if result.success:
                    ctx["tokens_used"] = result.meta.get("tokens_used")
                else:
                    ctx["error_category"] = result.error_category
        """
        if not self._enabled:
            yield {}
            return

        start_time = time.time()
        context: dict[str, Any] = {}

        try:
            yield context
            # Success if no exception raised
            duration = time.time() - start_time
            self.record_execution(
                agent_name=agent_name,
                status="success",
                duration_seconds=duration,
                tokens_used=context.get("tokens_used"),
            )

        except Exception:
            # Failure if exception raised
            duration = time.time() - start_time
            error_category = context.get("error_category", ErrorCategory.INTERNAL_ERROR)
            self.record_execution(
                agent_name=agent_name,
                status="fail",
                duration_seconds=duration,
                error_category=error_category,
            )
            raise

    def record_from_step_result(
        self,
        agent_name: str,
        result: StepResult,
    ) -> None:
        """Record metrics from StepResult.

        Extracts status, duration, error_category, and tokens from StepResult
        metadata and records appropriate metrics.

        Args:
            agent_name: Name of the agent that produced this result
            result: StepResult from agent execution
        """
        if not self._enabled:
            return

        try:
            # Determine status from StepResult
            status = "success" if result.success else "fail"

            # Extract metadata
            meta = result.meta or {}
            duration_seconds = meta.get("elapsed_ms", 0) / 1000.0 if "elapsed_ms" in meta else None
            error_category = result.error_category if hasattr(result, "error_category") else None

            # Extract token usage from resource_usage
            tokens_used = None
            if "resource_usage" in meta:
                usage = meta["resource_usage"]
                tokens_in = usage.get("tokens_in", 0)
                tokens_out = usage.get("tokens_out", 0)
                tokens_used = tokens_in + tokens_out if tokens_in or tokens_out else None

            self.record_execution(
                agent_name=agent_name,
                status=status,
                duration_seconds=duration_seconds,
                error_category=error_category,
                tokens_used=tokens_used,
            )

        except Exception:
            logger.debug("Failed to record metrics from StepResult")


__all__ = ["AgentMetricsCollector"]
