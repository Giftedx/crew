"""Minimal LangGraph pilot for ingest→analysis orchestration.

Gated by ENABLE_LANGGRAPH_PILOT. Import guards prevent hard dependency on
langgraph at runtime when the flag is off or the library isn't installed.
"""

from __future__ import annotations

import os
import time
from contextlib import nullcontext, suppress
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from ultimate_discord_intelligence_bot.obs import metrics, tracing


if TYPE_CHECKING:
    from collections.abc import Callable


def _resolve_tenancy():
    try:
        import importlib

        for name in (
            "ultimate_discord_intelligence_bot.tenancy.context",
            "src.ultimate_discord_intelligence_bot.tenancy.context",
        ):
            try:
                mod = importlib.import_module(name)
                _TenantContext = getattr(mod, "TenantContext", None)
                _current_tenant = getattr(mod, "current_tenant", None)
                _with_tenant = getattr(mod, "with_tenant", None)
                if _TenantContext and _current_tenant and _with_tenant:
                    return (_TenantContext, _current_tenant, _with_tenant)
            except Exception:
                continue
    except Exception:
        pass
    return (None, None, None)


TenantContext, current_tenant, with_tenant = _resolve_tenancy()
try:
    LANGGRAPH_AVAILABLE = True
except Exception:
    LANGGRAPH_AVAILABLE = False


@dataclass
class PilotConfig:
    enable: bool = False


def _is_enabled() -> bool:
    return os.getenv("ENABLE_LANGGRAPH_PILOT", "0").lower() in ("1", "true", "yes", "on")


class _Node:
    def __init__(self, name: str, fn: Callable[[dict[str, Any]], dict[str, Any]]):
        self.name = name
        self.fn = fn
        self.next: list[_Node] = []

    def then(self, other: _Node) -> _Node:
        self.next.append(other)
        return other


class _Graph:
    """A tiny DAG executor for linear flows used only when pilot flag is enabled.

    It executes nodes in BFS order starting from the provided root, threading a shared
    context dict and collecting per-node outputs into the provided `outputs` dict using
    the node name as the key.
    """

    def __init__(self, root: _Node):
        self.root = root

    def run(self, base_ctx: dict[str, Any], outputs: dict[str, Any]) -> None:
        visited: set[_Node] = set()
        queue: list[_Node] = [self.root]
        ctx: dict[str, Any] = dict(base_ctx)
        while queue:
            node = queue.pop(0)
            if node in visited:
                continue
            visited.add(node)
            res = node.fn(ctx)
            if isinstance(res, dict):
                ctx.update(res)
            outputs[node.name] = res
            queue.extend(node.next)


def run_ingest_analysis_pilot(
    job: dict[str, Any],
    ingest_fn: Callable[[dict[str, Any]], dict[str, Any]],
    analyze_fn: Callable[[dict[str, Any]], dict[str, Any]],
    *,
    segment_fn: Callable[[dict[str, Any]], dict[str, Any]] | None = None,
    embed_fn: Callable[[dict[str, Any]], dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Run a minimal ingest→analysis orchestration.

    Args:
        job: Base job context (e.g., {"tenant": ..., "workspace": ...}).
        ingest_fn: Function that produces ingest outputs (e.g., chunks, namespace).
        analyze_fn: Function that consumes accumulated context to produce analysis.
        segment_fn: Optional function to produce segmentation outputs; metrics step=segment recorded on success.
        embed_fn: Optional function to produce embedding outputs; metrics step=embed recorded on success.

    Behavior:
        - If ENABLE_LANGGRAPH_PILOT is disabled or library unavailable, falls back to sequential execution
          and records a degradation event (component=langgraph_pilot, event_type=fallback_sequential).
        - Always executes steps in order: ingest -> (segment?) -> (embed?) -> analyze.
        - Records step completion for step=langgraph_pilot after analyze.

    Returns:
        Dict containing step outputs and an 'orchestrator' label (langgraph_stub|sequential).
    """
    enabled = _is_enabled()
    orchestrator = "langgraph_stub" if enabled and LANGGRAPH_AVAILABLE else "sequential"
    _has_tenant_ctx = False
    _tenant_ctx_obj = None
    try:
        tenant_id = job.get("tenant") or job.get("tenant_id")
        workspace_id = job.get("workspace") or job.get("workspace_id")
        if (
            TenantContext
            and with_tenant
            and current_tenant
            and tenant_id
            and workspace_id
            and (current_tenant() is None)
        ):
            _tenant_ctx_obj = TenantContext(tenant_id, workspace_id)
            _has_tenant_ctx = True
    except Exception:
        _has_tenant_ctx = False
    with with_tenant(_tenant_ctx_obj) if _has_tenant_ctx and with_tenant else nullcontext():
        try:
            _labels = metrics.label_ctx()
            if _labels.get("tenant") == "unknown" or _labels.get("workspace") == "unknown":
                metrics.TENANCY_FALLBACKS.labels(**_labels, component="langgraph_pilot").inc()
        except Exception:
            pass
        with suppress(Exception):
            metrics.PIPELINE_REQUESTS.labels(**metrics.label_ctx()).inc()
        with suppress(Exception):
            metrics.PIPELINE_INFLIGHT.labels(**metrics.label_ctx(), orchestrator=orchestrator).inc()
        if orchestrator == "sequential":
            with suppress(Exception):
                metrics.DEGRADATION_EVENTS.labels(
                    **metrics.label_ctx(),
                    component="langgraph_pilot",
                    event_type="fallback_sequential",
                    severity="info",
                ).inc()
        try:
            if segment_fn is None:
                metrics.PIPELINE_STEPS_SKIPPED.labels(**metrics.label_ctx(), step="segment").inc()
            if embed_fn is None:
                metrics.PIPELINE_STEPS_SKIPPED.labels(**metrics.label_ctx(), step="embed").inc()
        except Exception:
            pass
    start_time = time.monotonic()
    _status = "success"
    outputs: dict[str, Any] = {}

    def _ingest_node(ctx: dict[str, Any]) -> dict[str, Any]:
        with tracing.start_span("langgraph_pilot.step.ingest") as step_span:
            if hasattr(step_span, "set_attribute"):
                step_span.set_attribute("orchestrator", orchestrator)
                step_span.set_attribute("step", "ingest")
            _step_start = time.monotonic()
            try:
                res = ingest_fn(ctx)
                with suppress(Exception):
                    metrics.PIPELINE_STEPS_COMPLETED.labels(**metrics.label_ctx(), step="ingest").inc()
                if hasattr(step_span, "set_attribute"):
                    step_span.set_attribute("outcome", "success")
                with suppress(Exception):
                    metrics.PIPELINE_STEP_DURATION.labels(
                        **metrics.label_ctx(), step="ingest", orchestrator=orchestrator, status="success"
                    ).observe(time.monotonic() - _step_start)
                return res
            except Exception:
                if hasattr(step_span, "set_attribute"):
                    step_span.set_attribute("outcome", "error")
                with suppress(Exception):
                    metrics.PIPELINE_STEPS_FAILED.labels(**metrics.label_ctx(), step="ingest").inc()
                with suppress(Exception):
                    metrics.PIPELINE_STEP_DURATION.labels(
                        **metrics.label_ctx(), step="ingest", orchestrator=orchestrator, status="error"
                    ).observe(time.monotonic() - _step_start)
                raise

    def _segment_node(ctx: dict[str, Any]) -> dict[str, Any]:
        assert segment_fn is not None
        with tracing.start_span("langgraph_pilot.step.segment") as step_span:
            if hasattr(step_span, "set_attribute"):
                step_span.set_attribute("orchestrator", orchestrator)
                step_span.set_attribute("step", "segment")
            _step_start = time.monotonic()
            try:
                res = segment_fn(ctx)
                with suppress(Exception):
                    metrics.PIPELINE_STEPS_COMPLETED.labels(**metrics.label_ctx(), step="segment").inc()
                if hasattr(step_span, "set_attribute"):
                    step_span.set_attribute("outcome", "success")
                with suppress(Exception):
                    metrics.PIPELINE_STEP_DURATION.labels(
                        **metrics.label_ctx(), step="segment", orchestrator=orchestrator, status="success"
                    ).observe(time.monotonic() - _step_start)
                return res
            except Exception:
                with suppress(Exception):
                    metrics.DEGRADATION_EVENTS.labels(
                        **metrics.label_ctx(),
                        component="langgraph_pilot",
                        event_type="segment_failure",
                        severity="error",
                    ).inc()
                if hasattr(step_span, "set_attribute"):
                    step_span.set_attribute("outcome", "error")
                with suppress(Exception):
                    metrics.PIPELINE_STEPS_FAILED.labels(**metrics.label_ctx(), step="segment").inc()
                with suppress(Exception):
                    metrics.PIPELINE_STEP_DURATION.labels(
                        **metrics.label_ctx(), step="segment", orchestrator=orchestrator, status="error"
                    ).observe(time.monotonic() - _step_start)
                return {}

    def _embed_node(ctx: dict[str, Any]) -> dict[str, Any]:
        assert embed_fn is not None
        with tracing.start_span("langgraph_pilot.step.embed") as step_span:
            if hasattr(step_span, "set_attribute"):
                step_span.set_attribute("orchestrator", orchestrator)
                step_span.set_attribute("step", "embed")
            _step_start = time.monotonic()
            try:
                res = embed_fn(ctx)
                with suppress(Exception):
                    metrics.PIPELINE_STEPS_COMPLETED.labels(**metrics.label_ctx(), step="embed").inc()
                if hasattr(step_span, "set_attribute"):
                    step_span.set_attribute("outcome", "success")
                with suppress(Exception):
                    metrics.PIPELINE_STEP_DURATION.labels(
                        **metrics.label_ctx(), step="embed", orchestrator=orchestrator, status="success"
                    ).observe(time.monotonic() - _step_start)
                return res
            except Exception:
                with suppress(Exception):
                    metrics.DEGRADATION_EVENTS.labels(
                        **metrics.label_ctx(), component="langgraph_pilot", event_type="embed_failure", severity="error"
                    ).inc()
                if hasattr(step_span, "set_attribute"):
                    step_span.set_attribute("outcome", "error")
                with suppress(Exception):
                    metrics.PIPELINE_STEPS_FAILED.labels(**metrics.label_ctx(), step="embed").inc()
                with suppress(Exception):
                    metrics.PIPELINE_STEP_DURATION.labels(
                        **metrics.label_ctx(), step="embed", orchestrator=orchestrator, status="error"
                    ).observe(time.monotonic() - _step_start)
                return {}

    def _analyze_node(ctx: dict[str, Any]) -> dict[str, Any]:
        with tracing.start_span("langgraph_pilot.step.analyze") as step_span:
            if hasattr(step_span, "set_attribute"):
                step_span.set_attribute("orchestrator", orchestrator)
                step_span.set_attribute("step", "analyze")
            _step_start = time.monotonic()
            try:
                res = analyze_fn(ctx)
                with suppress(Exception):
                    metrics.PIPELINE_STEPS_COMPLETED.labels(**metrics.label_ctx(), step="analyze").inc()
                if hasattr(step_span, "set_attribute"):
                    step_span.set_attribute("outcome", "success")
                with suppress(Exception):
                    metrics.PIPELINE_STEP_DURATION.labels(
                        **metrics.label_ctx(), step="analyze", orchestrator=orchestrator, status="success"
                    ).observe(time.monotonic() - _step_start)
                return res
            except Exception:
                if hasattr(step_span, "set_attribute"):
                    step_span.set_attribute("outcome", "error")
                with suppress(Exception):
                    metrics.PIPELINE_STEPS_FAILED.labels(**metrics.label_ctx(), step="analyze").inc()
                with suppress(Exception):
                    metrics.PIPELINE_STEP_DURATION.labels(
                        **metrics.label_ctx(), step="analyze", orchestrator=orchestrator, status="error"
                    ).observe(time.monotonic() - _step_start)
                raise

    with (
        with_tenant(_tenant_ctx_obj) if _has_tenant_ctx and with_tenant else nullcontext(),
        tracing.start_span("langgraph_pilot.run") as span,
    ):
        if hasattr(span, "set_attribute"):
            span.set_attribute("orchestrator", orchestrator)
            span.set_attribute("segment_enabled", str(segment_fn is not None))
            span.set_attribute("embed_enabled", str(embed_fn is not None))
        try:
            if orchestrator == "langgraph_stub":
                n_ingest = _Node("ingest", _ingest_node)
                current = n_ingest
                if segment_fn is not None:
                    n_segment = _Node("segment", _segment_node)
                    current = current.then(n_segment)
                if embed_fn is not None:
                    n_embed = _Node("embed", _embed_node)
                    current = current.then(n_embed)
                n_analyze = _Node("analysis", _analyze_node)
                current.then(n_analyze)
                _Graph(n_ingest).run(job, outputs)
            else:
                ingest_res = _ingest_node(job)
                outputs["ingest"] = ingest_res
                base_ctx = {**job, **ingest_res}
                if segment_fn is not None:
                    seg = _segment_node(base_ctx)
                    outputs["segment"] = seg
                    base_ctx.update(seg)
                else:
                    with suppress(Exception):
                        metrics.PIPELINE_STEPS_SKIPPED.labels(**metrics.label_ctx(), step="segment").inc()
                if embed_fn is not None:
                    emb = _embed_node(base_ctx)
                    outputs["embed"] = emb
                    base_ctx.update(emb)
                else:
                    with suppress(Exception):
                        metrics.PIPELINE_STEPS_SKIPPED.labels(**metrics.label_ctx(), step="embed").inc()
                analysis_res = _analyze_node(base_ctx)
                outputs["analysis"] = analysis_res
        except Exception:
            _status = "error"
            if hasattr(span, "set_attribute"):
                span.set_attribute("outcome", "error")
            raise
        finally:
            try:
                elapsed = time.monotonic() - start_time
                metrics.PIPELINE_DURATION.labels(**metrics.label_ctx(), status=_status).observe(elapsed)
                with suppress(Exception):
                    metrics.PIPELINE_TOTAL_DURATION.labels(
                        **metrics.label_ctx(), orchestrator=orchestrator, status=_status
                    ).observe(elapsed)
                with suppress(Exception):
                    metrics.PIPELINE_INFLIGHT.labels(**metrics.label_ctx(), orchestrator=orchestrator).dec()
                with suppress(Exception):
                    outputs["duration_seconds"] = elapsed
                if hasattr(span, "set_attribute"):
                    span.set_attribute("pipeline_duration_seconds", elapsed)
                    span.set_attribute("outcome", _status)
            except Exception:
                pass
    with with_tenant(_tenant_ctx_obj) if _has_tenant_ctx and with_tenant else nullcontext(), suppress(Exception):
        metrics.PIPELINE_STEPS_COMPLETED.labels(**metrics.label_ctx(), step="langgraph_pilot").inc()
    outputs["orchestrator"] = orchestrator
    return outputs


__all__ = ["PilotConfig", "run_ingest_analysis_pilot"]
