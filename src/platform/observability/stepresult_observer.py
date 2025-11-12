from __future__ import annotations

import json
import logging
import time
from functools import wraps
from typing import TYPE_CHECKING, Any, ParamSpec, TypeVar, cast

from ultimate_discord_intelligence_bot.step_result import StepResult

from ..settings import ENABLE_OBSERVABILITY_WRAPPER, ENABLE_OTEL_EXPORT
from ..tenancy.context import current_tenant


if TYPE_CHECKING:
    from collections.abc import Callable


P = ParamSpec("P")
R = TypeVar("R", bound=StepResult)


def _safe_json(obj: Any) -> str:
    try:
        return json.dumps(obj, ensure_ascii=False, default=str)
    except Exception:
        return "{}"


def observe_step_result(
    tool_name: str | None = None,
) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """Decorator to record structured logs for StepResult-returning callables.

    When ENABLE_OBSERVABILITY_WRAPPER is disabled the decorator becomes a no-op.
    """

    def decorator(func: Callable[P, R]) -> Callable[P, R]:
        if not ENABLE_OBSERVABILITY_WRAPPER:
            return func

        logger = logging.getLogger("observability")

        @wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            start = time.perf_counter()
            tenant_ctx = current_tenant()
            tenant = getattr(tenant_ctx, "tenant", "unknown") if tenant_ctx else "unknown"
            workspace = getattr(tenant_ctx, "workspace", "unknown") if tenant_ctx else "unknown"
            name = tool_name or getattr(func, "__qualname__", getattr(func, "__name__", "unknown"))
            try:
                result = func(*args, **kwargs)
                duration_ms = (time.perf_counter() - start) * 1000.0
                payload = {
                    "event": "stepresult",
                    "tool": name,
                    "success": bool(getattr(result, "success", True)),
                    "status": getattr(result, "status", None),
                    "error": getattr(result, "error", None),
                    "tenant": tenant,
                    "workspace": workspace,
                    "duration_ms": duration_ms,
                }
                logger.info(_safe_json(payload))

                # Optional OpenTelemetry hook (no hard dependency)
                if ENABLE_OTEL_EXPORT:
                    try:
                        from opentelemetry import trace

                        tracer = trace.get_tracer("udi.observer")
                        with tracer.start_as_current_span(f"{name}") as span:
                            span.set_attribute("udi.tool", name)
                            span.set_attribute("udi.tenant", tenant)
                            span.set_attribute("udi.workspace", workspace)
                            span.set_attribute("udi.duration_ms", duration_ms)
                            span.set_attribute("udi.success", bool(getattr(result, "success", False)))
                            err = getattr(result, "error", None)
                            if err:
                                span.set_attribute("udi.error", str(err))
                    except Exception:  # pragma: no cover - best-effort
                        pass

                return cast("R", result)
            except Exception as exc:
                duration_ms = (time.perf_counter() - start) * 1000.0
                payload = {
                    "event": "stepresult",
                    "tool": name,
                    "success": False,
                    "status": "exception",
                    "error": str(exc),
                    "tenant": tenant,
                    "workspace": workspace,
                    "duration_ms": duration_ms,
                }
                logger.error(_safe_json(payload))
                raise

        return wrapper

    return decorator
