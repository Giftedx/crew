from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from core.time import default_utc_now
from ultimate_discord_intelligence_bot.obs.metrics import get_metrics

from .middleware import Middleware
from .step import Step


class Executor:
    """Runs a Step with a middleware chain and basic observability.

    This scaffolding has no coupling to existing pipelines; it's opt-in.
    """

    def __init__(self, middleware: Iterable[Middleware] | None = None) -> None:
        self._middleware = list(middleware or [])
        self._metrics = get_metrics()

    def execute(self, step: Step, context: dict[str, Any]) -> dict[str, Any]:
        # Ensure UTC timestamp context for consistency
        context.setdefault("started_at", default_utc_now().isoformat())

        # Before hooks
        for m in self._middleware:
            try:
                m.before(context)
            except Exception:
                # Middleware must not break execution; continue
                pass

        # Execute step
        try:
            result = step.run(context)
        except Exception as e:  # Error path hooks
            for m in self._middleware:
                try:
                    m.on_error(context, e)
                except Exception:
                    pass
            raise

        # After hooks
        for m in self._middleware:
            try:
                m.after(context, result)
            except Exception:
                pass

        # Emit basic metric (low-cardinality)
        try:
            self._metrics.counter(
                "pipeline_step_executed_total",
                description="Count of executed pipeline steps",
            ).add(1, {"idempotent": str(getattr(step, "idempotent", False))})
        except Exception:
            pass

        return result
