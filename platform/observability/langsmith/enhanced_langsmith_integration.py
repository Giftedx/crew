"""Enhanced LangSmith integration for comprehensive LLM observability.

This module provides specialized LLM tracing and evaluation capabilities
to complement the existing OpenTelemetry observability infrastructure.
"""

from __future__ import annotations

import logging
import time
import uuid
from typing import TYPE_CHECKING, Any

from core.secure_config import get_config
from core.time import default_utc_now

from ultimate_discord_intelligence_bot.tenancy.context import current_tenant


logger = logging.getLogger(__name__)

if TYPE_CHECKING:  # pragma: no cover - typing only
    from langsmith import Client as _LSClient
    from langsmith.schemas import Example as _LSExample
else:
    _LSClient = Any
    _LSExample = Any

try:
    # Import only to detect availability; keep types separate to avoid runtime/type coupling
    from langsmith import Client as _RuntimeClient  # noqa: F401
    from langsmith.schemas import Example as _RuntimeExample  # noqa: F401

    LANGSMITH_AVAILABLE = True
    logger.info("LangSmith integration available")
except ImportError:  # pragma: no cover
    LANGSMITH_AVAILABLE = False
    logger.debug("LangSmith not available - specialized LLM tracing disabled")

# imports moved above to satisfy E402


class LangSmithObservabilityManager:
    """Manager for LangSmith-based LLM observability."""

    def __init__(self):
        """Initialize LangSmith client if configured."""
        self.client: _LSClient | None = None
        self.enabled = False

        if LANGSMITH_AVAILABLE:
            try:
                config = get_config()
                api_key = getattr(config, "langsmith_api_key", None)
                project_name = getattr(config, "langsmith_project", "ultimate-discord-bot")

                if api_key:
                    # Runtime import guarded by availability
                    from langsmith import Client as _Client

                    self.client = _Client(api_key=api_key)
                    self.project_name = project_name
                    self.enabled = True
                    logger.info(f"LangSmith observability enabled for project: {project_name}")
                else:
                    logger.info("LangSmith API key not configured - specialized tracing disabled")

            except Exception as e:
                logger.warning(f"Failed to initialize LangSmith client: {e}")
        else:
            logger.debug("LangSmith not available")

    def trace_llm_call(
        self,
        name: str,
        prompt: str,
        response: str,
        model: str,
        metadata: dict[str, Any] | None = None,
        latency_ms: float | None = None,
        token_usage: dict[str, int] | None = None,
        cost: float | None = None,
        error: str | None = None,
    ) -> str | None:
        """Trace an LLM call with comprehensive metadata."""
        if not self.enabled or not self.client:
            return None

        try:
            # Get tenant context for multi-tenant tracing
            ctx = current_tenant()
            tenant_id = ctx.tenant_id if ctx else "default"
            workspace = ctx.workspace_id if ctx else "main"

            # Build comprehensive inputs
            inputs = {
                "prompt": prompt,
                "model": model,
                "tenant": tenant_id,
                "workspace": workspace,
            }

            if metadata:
                inputs.update(metadata)

            # Build outputs
            outputs = {"response": response} if not error else {"error": error}

            # Build extra metadata
            extra = {
                "model": model,
                "tenant": tenant_id,
                "workspace": workspace,
                "timestamp": default_utc_now().isoformat(),
            }

            if latency_ms is not None:
                extra["latency_ms"] = str(latency_ms)

            if token_usage:
                extra["token_usage"] = str(token_usage)

            if cost is not None:
                extra["cost_usd"] = str(cost)

            # Create run
            run_id = str(uuid.uuid4())

            self.client.create_run(
                id=run_id,
                name=name,
                project_name=self.project_name,
                run_type="llm",
                inputs=inputs,
                outputs=outputs,
                extra=extra,
                start_time=default_utc_now(),
                end_time=default_utc_now(),
                error=error,
            )

            logger.debug(f"Traced LLM call to LangSmith: {name} (run_id: {run_id})")
            return run_id

        except Exception as e:
            logger.error(f"Failed to trace LLM call to LangSmith: {e}")
            return None

    def trace_tool_execution(
        self,
        tool_name: str,
        inputs: dict[str, Any],
        outputs: dict[str, Any],
        latency_ms: float,
        error: str | None = None,
    ) -> str | None:
        """Trace tool execution for complete workflow visibility."""
        if not self.enabled or not self.client:
            return None

        try:
            ctx = current_tenant()
            tenant_id = ctx.tenant_id if ctx else "default"
            workspace = ctx.workspace_id if ctx else "main"

            extra = {
                "tool_name": tool_name,
                "tenant": tenant_id,
                "workspace": workspace,
                "latency_ms": latency_ms,
                "timestamp": default_utc_now().isoformat(),
            }

            run_id = str(uuid.uuid4())

            self.client.create_run(
                id=run_id,
                name=f"tool_{tool_name}",
                project_name=self.project_name,
                run_type="tool",
                inputs=inputs,
                outputs=outputs,
                extra=extra,
                start_time=default_utc_now(),
                end_time=default_utc_now(),
                error=error,
            )

            logger.debug(f"Traced tool execution to LangSmith: {tool_name} (run_id: {run_id})")
            return run_id

        except Exception as e:
            logger.error(f"Failed to trace tool execution to LangSmith: {e}")
            return None

    def trace_pipeline_execution(
        self,
        pipeline_name: str,
        steps: list[dict[str, Any]],
        inputs: dict[str, Any],
        outputs: dict[str, Any],
        total_latency_ms: float,
        error: str | None = None,
    ) -> str | None:
        """Trace complete pipeline execution with step breakdown."""
        if not self.enabled or not self.client:
            return None

        try:
            ctx = current_tenant()
            tenant_id = ctx.tenant_id if ctx else "default"
            workspace = ctx.workspace_id if ctx else "main"

            # Create parent run for pipeline
            parent_run_id = str(uuid.uuid4())

            extra = {
                "pipeline_name": pipeline_name,
                "tenant": tenant_id,
                "workspace": workspace,
                "total_latency_ms": total_latency_ms,
                "step_count": len(steps),
                "timestamp": default_utc_now().isoformat(),
            }

            # Create parent pipeline run
            self.client.create_run(
                id=parent_run_id,
                name=f"pipeline_{pipeline_name}",
                project_name=self.project_name,
                run_type="chain",
                inputs=inputs,
                outputs=outputs,
                extra=extra,
                start_time=default_utc_now(),
                end_time=default_utc_now(),
                error=error,
            )

            # Create child runs for each step
            for i, step in enumerate(steps):
                step_run_id = str(uuid.uuid4())

                self.client.create_run(
                    id=step_run_id,
                    parent_run_id=parent_run_id,
                    name=f"step_{i}_{step.get('name', 'unknown')}",
                    project_name=self.project_name,
                    run_type="chain",
                    inputs=step.get("inputs", {}),
                    outputs=step.get("outputs", {}),
                    extra={
                        "step_index": i,
                        "step_name": step.get("name", "unknown"),
                        "latency_ms": step.get("latency_ms", 0),
                        "tenant": tenant_id,
                        "workspace": workspace,
                    },
                    start_time=default_utc_now(),
                    end_time=default_utc_now(),
                    error=step.get("error"),
                )

            logger.debug(f"Traced pipeline execution to LangSmith: {pipeline_name} (run_id: {parent_run_id})")
            return parent_run_id

        except Exception as e:
            logger.error(f"Failed to trace pipeline execution to LangSmith: {e}")
            return None

    def create_evaluation_dataset(
        self,
        dataset_name: str,
        examples: list[dict[str, Any]],
        description: str = "",
    ) -> str | None:
        """Create evaluation dataset for model performance tracking."""
        if not self.enabled or not self.client:
            return None

        try:
            # Create dataset
            dataset = self.client.create_dataset(
                dataset_name=dataset_name,
                description=description,
            )

            # Add examples to dataset
            dataset_examples: list[_LSExample] = []
            for example in examples:
                # Only executed when LangSmith is available; Example exists at runtime
                from langsmith.schemas import Example as _Example

                example_obj = _Example(
                    inputs=example.get("inputs", {}),
                    outputs=example.get("outputs", {}),
                    metadata=example.get("metadata", {}),
                )
                dataset_examples.append(example_obj)

            self.client.create_examples(
                inputs=[ex.inputs for ex in dataset_examples],
                outputs=[ex.outputs for ex in dataset_examples],
                metadata=[ex.metadata for ex in dataset_examples],
                dataset_id=dataset.id,
            )

            logger.info(f"Created LangSmith evaluation dataset: {dataset_name} with {len(examples)} examples")
            return str(dataset.id)

        except Exception as e:
            logger.error(f"Failed to create LangSmith evaluation dataset: {e}")
            return None

    def run_evaluation(
        self,
        dataset_name: str,
        evaluator_function: Any,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any] | None:
        """Run evaluation against a dataset."""
        if not self.enabled or not self.client:
            return None

        try:
            # This would integrate with LangSmith's evaluation framework
            # Implementation depends on specific evaluation requirements
            logger.info(f"Running evaluation on dataset: {dataset_name}")

            # Placeholder for evaluation results
            results = {
                "dataset_name": dataset_name,
                "evaluation_time": default_utc_now().isoformat(),
                "metadata": metadata or {},
            }

            return results

        except Exception as e:
            logger.error(f"Failed to run LangSmith evaluation: {e}")
            return None

    def get_project_analytics(self, days: int = 7) -> dict[str, Any] | None:
        """Get analytics data for the project."""
        if not self.enabled or not self.client:
            return None

        try:
            # Get project runs for analytics
            # This would use LangSmith's analytics API
            analytics = {
                "project_name": self.project_name,
                "period_days": days,
                "timestamp": default_utc_now().isoformat(),
                # Placeholder for actual analytics data
                "total_runs": 0,
                "error_rate": 0.0,
                "avg_latency_ms": 0.0,
                "total_cost_usd": 0.0,
            }

            logger.debug(f"Retrieved LangSmith analytics for project: {self.project_name}")
            return analytics

        except Exception as e:
            logger.error(f"Failed to get LangSmith analytics: {e}")
            return None


# Global instance for easy access
_langsmith_manager: LangSmithObservabilityManager | None = None


def get_langsmith_manager() -> LangSmithObservabilityManager:
    """Get the global LangSmith observability manager."""
    global _langsmith_manager
    if _langsmith_manager is None:
        _langsmith_manager = LangSmithObservabilityManager()
    return _langsmith_manager


def trace_llm_call(name: str, prompt: str, response: str, model: str, **kwargs) -> str | None:
    """Convenience function for tracing LLM calls."""
    manager = get_langsmith_manager()
    return manager.trace_llm_call(name, prompt, response, model, **kwargs)


def trace_tool_execution(
    tool_name: str,
    inputs: dict[str, Any],
    outputs: dict[str, Any],
    latency_ms: float,
    **kwargs,
) -> str | None:
    """Convenience function for tracing tool executions."""
    manager = get_langsmith_manager()
    return manager.trace_tool_execution(tool_name, inputs, outputs, latency_ms, **kwargs)


# Decorator for automatic tool tracing
def traced_tool(tool_name: str):
    """Decorator to automatically trace tool execution."""

    def decorator(func):
        def wrapper(*args, **kwargs):
            start_time = time.time()
            error = None

            try:
                result = func(*args, **kwargs)
                outputs = {"result": result} if not isinstance(result, dict) else result
            except Exception as e:
                error = str(e)
                outputs = {"error": error}
                raise
            finally:
                latency_ms = (time.time() - start_time) * 1000

                # Build inputs from function arguments
                inputs = {
                    "args": args,
                    "kwargs": {k: v for k, v in kwargs.items() if not callable(v)},
                }

                trace_tool_execution(
                    tool_name=tool_name,
                    inputs=inputs,
                    outputs=outputs,
                    latency_ms=latency_ms,
                    error=error,
                )

            return result

        return wrapper

    return decorator
