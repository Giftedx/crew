from __future__ import annotations

import contextlib
from typing import TYPE_CHECKING, Any

from core.time import default_utc_now
from ultimate_discord_intelligence_bot.obs.metrics import get_metrics


if TYPE_CHECKING:
    from collections.abc import Iterable

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
            with contextlib.suppress(Exception):
                m.before(context)

        # Execute step
        try:
            result = step.run(context)
        except Exception as e:  # Error path hooks
            for m in self._middleware:
                with contextlib.suppress(Exception):
                    m.on_error(context, e)
            raise

        # After hooks
        for m in self._middleware:
            with contextlib.suppress(Exception):
                m.after(context, result)

        # Emit basic metric (low-cardinality)
        with contextlib.suppress(Exception):
            self._metrics.counter(
                "pipeline_step_executed_total",
                description="Count of executed pipeline steps",
            ).add(1, {"idempotent": str(getattr(step, "idempotent", False))})

        return result
