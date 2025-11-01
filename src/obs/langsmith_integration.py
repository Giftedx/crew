"""
LangSmith integration for comprehensive LLM observability and debugging.

This module provides enhanced observability specifically tailored for LLM applications,
including prompt tracking, response quality monitoring, and cost optimization analytics.
"""

from __future__ import annotations

import json
import logging
import time
import uuid
from contextlib import contextmanager
from dataclasses import asdict, dataclass
from typing import TYPE_CHECKING, Any

from core.secure_config import get_config
from obs import metrics
from ultimate_discord_intelligence_bot.tenancy.context import current_tenant


# Optional LangSmith dependency handling.
# We define LANGSMITH_AVAILABLE in all branches to avoid NameError at runtime
# and provide minimal stubs when the package is absent.
LANGSMITH_AVAILABLE = False
if TYPE_CHECKING:  # pragma: no cover - type checking only
    from collections.abc import Generator

    from langsmith import Client, RunTree
    from langsmith.run_trees import RunTree as LangSmithRunTree

    LANGSMITH_AVAILABLE = True
else:  # runtime import attempt
    try:
        from langsmith import Client, RunTree  # type: ignore[import-not-found]
        from langsmith.run_trees import RunTree as LangSmithRunTree  # type: ignore[import-not-found]

        LANGSMITH_AVAILABLE = True
    except Exception:  # pragma: no cover - absence path
        # Provide lightweight stubs so attribute access doesn't explode; we do NOT
        # mimic full behavior—only what's used here.
        class _RunTreeStub:  # minimal stub used when LangSmith isn't installed
            def __init__(self, *_, **__):
                pass

            def end(self, *_, **__):  # pragma: no cover - trivial
                pass

        # Assign stub classes so type checkers see objects (runtime only path)
        RunTree = _RunTreeStub  # type: ignore[assignment]
        LangSmithRunTree = _RunTreeStub  # type: ignore[assignment]

        class _ClientStub:  # minimal Client stub
            def __init__(self, *_, **__):
                pass

            def list_runs(self, *_, **__):  # pragma: no cover - trivial
                return []

        Client = _ClientStub  # type: ignore[assignment]


logger = logging.getLogger(__name__)


@dataclass
class LLMTrace:
    """Structured trace data for LLM interactions."""

    trace_id: str
    run_id: str
    model: str
    provider: str
    prompt: str
    response: str
    tokens_input: int
    tokens_output: int
    cost: float
    latency_ms: float
    task_type: str
    tenant_id: str | None
    workspace: str | None
    timestamp: float
    status: str
    error_message: str | None = None
    metadata: dict[str, Any] | None = None


@dataclass
class LLMMetrics:
    """Aggregated metrics for LLM performance analysis."""

    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    total_cost: float = 0.0
    total_tokens_input: int = 0
    total_tokens_output: int = 0
    average_latency: float = 0.0
    cost_per_token: float = 0.0
    success_rate: float = 0.0


class EnhancedLLMObservability:
    """Enhanced LLM observability with LangSmith integration."""

    def __init__(
        self,
        project_name: str = "ultimate-discord-intelligence-bot",
        enable_langsmith: bool = True,
        enable_local_tracing: bool = True,
    ):
        """Initialize enhanced LLM observability.

        Args:
            project_name: LangSmith project name for organizing traces
            enable_langsmith: Whether to use LangSmith cloud tracing
            enable_local_tracing: Whether to maintain local trace storage
        """
        self.project_name = project_name
        self.enable_langsmith = enable_langsmith and LANGSMITH_AVAILABLE
        self.enable_local_tracing = enable_local_tracing

        # Initialize LangSmith client if available
        self.langsmith_client: Client | None = None
        if self.enable_langsmith:
            try:
                self.langsmith_client = self._initialize_langsmith()
                logger.info("LangSmith observability initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize LangSmith: {e}")
                self.enable_langsmith = False

        # Local trace storage for analysis
        self.local_traces: list[LLMTrace] = []
        self.metrics = LLMMetrics()

        # Performance tracking
        self._active_runs: dict[str, dict[str, Any]] = {}

    def _initialize_langsmith(self) -> Client | None:
        """Initialize LangSmith client with proper configuration."""
        try:
            config = get_config()

            # Try to get LangSmith API key
            api_key = getattr(config, "langsmith_api_key", None)
            if not api_key:
                logger.warning("LangSmith API key not found in configuration")
                return None

            # Initialize client
            client = Client(
                api_key=api_key,
                api_url=getattr(config, "langsmith_api_url", "https://api.smith.langchain.com"),
            )

            # Test connection
            try:
                client.list_runs(project_name=self.project_name, limit=1)
                logger.info(f"LangSmith client initialized for project: {self.project_name}")
                return client
            except Exception as e:
                logger.warning(f"LangSmith connection test failed: {e}")
                return None

        except Exception as e:
            logger.error(f"Failed to initialize LangSmith client: {e}")
            return None

    @contextmanager
    def trace_llm_call(
        self,
        model: str,
        provider: str,
        task_type: str = "general",
        metadata: dict[str, Any] | None = None,
    ) -> Generator[dict[str, Any], None, None]:
        """Context manager for tracing LLM calls with comprehensive observability.

        Args:
            model: Model name being used
            provider: Provider name (openai, anthropic, etc.)
            task_type: Type of task being performed
            metadata: Additional metadata to include in trace

        Yields:
            Dictionary containing run context and tracing utilities
        """
        trace_id = str(uuid.uuid4())
        run_id = str(uuid.uuid4())
        start_time = time.perf_counter()

        # Get tenant context
        tenant_ctx = current_tenant()
        tenant_id = tenant_ctx.tenant_id if tenant_ctx else None
        workspace = tenant_ctx.workspace_id if tenant_ctx else None

        # Initialize run context
        run_context = {
            "trace_id": trace_id,
            "run_id": run_id,
            "model": model,
            "provider": provider,
            "task_type": task_type,
            "tenant_id": tenant_id,
            "workspace": workspace,
            "metadata": metadata or {},
            "start_time": start_time,
        }

        # Start LangSmith run if enabled
        langsmith_run = None
        if self.langsmith_client:
            try:
                langsmith_run = RunTree(
                    name=f"llm_call_{task_type}",
                    run_type="llm",
                    project_name=self.project_name,
                    tags=[provider, model, task_type],
                    extra={
                        "model": model,
                        "provider": provider,
                        "tenant_id": tenant_id,
                        "workspace": workspace,
                        **(metadata or {}),
                    },
                )
                run_context["langsmith_run"] = langsmith_run
            except Exception as e:
                logger.warning(f"Failed to start LangSmith run: {e}")

        # Store active run
        self._active_runs[run_id] = run_context

        try:
            yield run_context

            # Mark as successful if no exception
            run_context["status"] = "success"

        except Exception as e:
            # Mark as failed and capture error
            run_context["status"] = "error"
            run_context["error_message"] = str(e)

            if langsmith_run:
                try:
                    langsmith_run.end(error=str(e))
                except Exception as log_err:
                    logger.warning(f"Failed to log error to LangSmith: {log_err}")

            raise

        finally:
            # Calculate final metrics
            end_time = time.perf_counter()
            latency_ms = (end_time - start_time) * 1000

            # Finalize trace
            self._finalize_trace(run_context, latency_ms)

            # Clean up
            self._active_runs.pop(run_id, None)

    def _finalize_trace(self, run_context: dict[str, Any], latency_ms: float):
        """Finalize and store trace data."""
        try:
            # Extract data from context
            prompt = run_context.get("prompt", "")
            response = run_context.get("response", "")
            tokens_input = run_context.get("tokens_input", 0)
            tokens_output = run_context.get("tokens_output", 0)
            cost = run_context.get("cost", 0.0)

            # Create trace record
            trace = LLMTrace(
                trace_id=run_context["trace_id"],
                run_id=run_context["run_id"],
                model=run_context["model"],
                provider=run_context["provider"],
                prompt=prompt,
                response=response,
                tokens_input=tokens_input,
                tokens_output=tokens_output,
                cost=cost,
                latency_ms=latency_ms,
                task_type=run_context["task_type"],
                tenant_id=run_context.get("tenant_id"),
                workspace=run_context.get("workspace"),
                timestamp=time.time(),
                status=run_context.get("status", "unknown"),
                error_message=run_context.get("error_message"),
                metadata=run_context.get("metadata"),
            )

            # Store locally if enabled
            if self.enable_local_tracing:
                self.local_traces.append(trace)

                # Limit local storage size
                if len(self.local_traces) > 10000:
                    self.local_traces = self.local_traces[-5000:]  # Keep most recent 5000

            # Update aggregate metrics
            self._update_metrics(trace)

            # Finalize LangSmith run
            if "langsmith_run" in run_context:
                try:
                    langsmith_run = run_context["langsmith_run"]
                    langsmith_run.inputs = {"prompt": prompt}
                    langsmith_run.outputs = {"response": response}
                    langsmith_run.extra.update(
                        {
                            "tokens_input": tokens_input,
                            "tokens_output": tokens_output,
                            "cost": cost,
                            "latency_ms": latency_ms,
                        }
                    )

                    if trace.status == "success":
                        langsmith_run.end()
                    else:
                        langsmith_run.end(error=trace.error_message)

                except Exception as e:
                    logger.warning(f"Failed to finalize LangSmith run: {e}")

            # Update OpenTelemetry metrics
            self._update_otel_metrics(trace)

        except Exception as e:
            logger.error(f"Failed to finalize trace: {e}")

    def _update_metrics(self, trace: LLMTrace):
        """Update aggregate metrics with new trace data."""
        self.metrics.total_requests += 1

        if trace.status == "success":
            self.metrics.successful_requests += 1
        else:
            self.metrics.failed_requests += 1

        self.metrics.total_cost += trace.cost
        self.metrics.total_tokens_input += trace.tokens_input
        self.metrics.total_tokens_output += trace.tokens_output

        # Update averages
        total_latency = self.metrics.average_latency * (self.metrics.total_requests - 1)
        self.metrics.average_latency = (total_latency + trace.latency_ms) / self.metrics.total_requests

        total_tokens = self.metrics.total_tokens_input + self.metrics.total_tokens_output
        if total_tokens > 0:
            self.metrics.cost_per_token = self.metrics.total_cost / total_tokens

        if self.metrics.total_requests > 0:
            self.metrics.success_rate = self.metrics.successful_requests / self.metrics.total_requests

    def _update_otel_metrics(self, trace: LLMTrace):
        """Update OpenTelemetry metrics."""
        try:
            # Update existing metrics
            metrics.LLM_LATENCY.labels(**metrics.label_ctx()).observe(trace.latency_ms)
            metrics.LLM_ESTIMATED_COST.labels(
                **metrics.label_ctx(), model=trace.model, provider=trace.provider
            ).observe(trace.cost)

            if trace.status == "success":
                metrics.LLM_MODEL_SELECTED.labels(
                    **metrics.label_ctx(),
                    task=trace.task_type,
                    model=trace.model,
                    provider=trace.provider,
                ).inc()

        except Exception as e:
            logger.warning(f"Failed to update OpenTelemetry metrics: {e}")

    def log_llm_interaction(
        self,
        run_context: dict[str, Any],
        prompt: str,
        response: str,
        tokens_input: int,
        tokens_output: int,
        cost: float,
    ):
        """Log LLM interaction within an active trace context."""
        run_context.update(
            {
                "prompt": prompt,
                "response": response,
                "tokens_input": tokens_input,
                "tokens_output": tokens_output,
                "cost": cost,
            }
        )

    def get_metrics(self) -> LLMMetrics:
        """Get current aggregate metrics."""
        return self.metrics

    def get_traces(
        self,
        limit: int = 100,
        task_type: str | None = None,
        tenant_id: str | None = None,
        status: str | None = None,
    ) -> list[LLMTrace]:
        """Get recent traces with optional filtering."""
        traces = self.local_traces

        # Apply filters
        if task_type:
            traces = [t for t in traces if t.task_type == task_type]
        if tenant_id:
            traces = [t for t in traces if t.tenant_id == tenant_id]
        if status:
            traces = [t for t in traces if t.status == status]

        # Return most recent traces
        return sorted(traces, key=lambda t: t.timestamp, reverse=True)[:limit]

    def analyze_performance(self, lookback_hours: int = 24) -> dict[str, Any]:
        """Analyze LLM performance over specified time window."""
        cutoff_time = time.time() - (lookback_hours * 3600)
        recent_traces = [t for t in self.local_traces if t.timestamp > cutoff_time]

        if not recent_traces:
            return {"error": "No traces found in time window"}

        # Calculate performance metrics
        total_cost = sum(t.cost for t in recent_traces)
        avg_latency = sum(t.latency_ms for t in recent_traces) / len(recent_traces)
        success_rate = sum(1 for t in recent_traces if t.status == "success") / len(recent_traces)

        # Group by model
        model_stats = {}
        for trace in recent_traces:
            if trace.model not in model_stats:
                model_stats[trace.model] = {
                    "requests": 0,
                    "cost": 0.0,
                    "avg_latency": 0.0,
                    "success_rate": 0.0,
                }

            stats = model_stats[trace.model]
            stats["requests"] += 1
            stats["cost"] += trace.cost
            stats["avg_latency"] += trace.latency_ms
            if trace.status == "success":
                stats["success_rate"] += 1

        # Finalize model stats
        for stats in model_stats.values():
            stats["avg_latency"] /= stats["requests"]
            stats["success_rate"] /= stats["requests"]

        return {
            "time_window_hours": lookback_hours,
            "total_requests": len(recent_traces),
            "total_cost": total_cost,
            "average_latency_ms": avg_latency,
            "success_rate": success_rate,
            "model_breakdown": model_stats,
            "cost_per_request": total_cost / len(recent_traces) if recent_traces else 0,
        }

    def export_traces(self, fmt: str = "json") -> str:
        """Export traces in specified format for external analysis."""
        if fmt == "json":
            return json.dumps([asdict(trace) for trace in self.local_traces], indent=2)
        elif fmt == "csv":
            # Simple CSV export
            import csv
            import io

            output = io.StringIO()
            if self.local_traces:
                writer = csv.DictWriter(output, fieldnames=asdict(self.local_traces[0]).keys())
                writer.writeheader()
                for trace in self.local_traces:
                    writer.writerow(asdict(trace))

            return output.getvalue()
        else:
            raise ValueError(f"Unsupported export format: {fmt}")


# Global observability instance
_enhanced_observability: EnhancedLLMObservability | None = None


def get_enhanced_observability() -> EnhancedLLMObservability:
    """Get or create global enhanced observability instance."""
    global _enhanced_observability

    if _enhanced_observability is None:
        _enhanced_observability = EnhancedLLMObservability()

    return _enhanced_observability


__all__ = [
    "EnhancedLLMObservability",
    "LLMMetrics",
    "LLMTrace",
    "get_enhanced_observability",
]
