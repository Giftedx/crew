"""Multi-agent Research and Brief tool (guarded, offline-safe fallback).

Combines the offline ResearchAndBriefTool with an optional multi-agent
orchestration path via EnhancedCrewExecutor. The offline synthesis ensures
deterministic output; the multi-agent path augments metadata (quality/time).

Strict guardrails:
- Time limit enforced via asyncio.wait_for inside a background thread.
- Disabled entirely if imports fail or feature flags disallow crew usage.

Inputs:
- query: str
- sources_text: list[str] | None
- max_items: int = 5
- max_time: float = 60.0 (seconds budget for multi-agent path)
- enable_alerts: bool = False (keep overhead low by default)

Outputs: StepResult.ok with data matching the offline tool, plus meta field:
{
  outline, key_findings, citations, risks, counts,
  meta: {
    multi_agent: bool,
    quality_score: float | null,
    execution_time: float | null,
  }
}
"""

from __future__ import annotations
import contextlib
import threading
from queue import Queue
from typing import Any
from platform.observability.metrics import get_metrics
from platform.core.step_result import StepResult
from ._base import BaseTool
from .research_and_brief_tool import ResearchAndBriefTool


def _is_enabled(name: str, default: bool = True) -> bool:
    try:
        from platform.config.configuration import get_config

        v = get_config(name)
    except Exception:
        v = None
    if v is None:
        import os

        v = os.getenv(name)
    if v is None:
        return bool(default)
    return str(v).lower() in ("1", "true", "yes", "on")


class ResearchAndBriefMultiTool(BaseTool[StepResult]):
    name: str = "Research and Brief (Multi-Agent)"
    description: str = (
        "Synthesizes a brief from sources with an offline core, optionally augmented by a multi-agent run."
    )

    def __init__(self) -> None:
        super().__init__()
        self._metrics = get_metrics()
        self._offline = ResearchAndBriefTool()

    def _run_multi_agent(self, inputs: dict[str, Any], timeout: float) -> dict[str, Any] | None:
        """Run EnhancedCrewExecutor.execute_with_comprehensive_monitoring in a background thread.

        Returns the executor result dict or None on failure/disable.
        """
        if not _is_enabled("ENABLE_RESEARCH_AND_BRIEF_MULTI_AGENT", True):
            return None
        try:
            from ultimate_discord_intelligence_bot.enhanced_crew_integration import EnhancedCrewExecutor

            out_q: Queue[dict[str, Any] | BaseException | None] = Queue(maxsize=1)

            def worker() -> None:
                import asyncio

                async def _runner() -> dict[str, Any]:
                    executor = EnhancedCrewExecutor()
                    return await executor.execute_with_comprehensive_monitoring(
                        inputs=inputs, enable_real_time_alerts=False, quality_threshold=0.7, max_execution_time=timeout
                    )

                try:
                    result = asyncio.run(asyncio.wait_for(_runner(), timeout=timeout))
                    out_q.put(result)
                except BaseException as exc:
                    out_q.put(exc)

            t = threading.Thread(target=worker, daemon=True)
            t.start()
            t.join(timeout + 5.0)
            if not t.is_alive():
                item = out_q.get_nowait()
                if isinstance(item, BaseException):
                    return None
                return item
            return None
        except Exception:
            return None

    def run(
        self,
        *,
        query: str,
        sources_text: list[str] | None = None,
        max_items: int = 5,
        max_time: float = 60.0,
        enable_alerts: bool = False,
    ) -> StepResult:
        offline_sr = self._offline.run(query=query, sources_text=sources_text, max_items=max_items)
        base_data = offline_sr.data if isinstance(offline_sr.data, dict) else {}
        meta = {"multi_agent": False, "quality_score": None, "execution_time": None}
        ma_inputs = {"query": query, "sources_text": sources_text, "max_items": max_items}
        ma_result = self._run_multi_agent(ma_inputs, timeout=float(max_time))
        if isinstance(ma_result, dict):
            meta["multi_agent"] = True
            meta["quality_score"] = float(ma_result.get("quality_score") or 0.0)
            meta["execution_time"] = float(ma_result.get("execution_time") or 0.0)
        data = dict(base_data)
        data["meta"] = meta
        with contextlib.suppress(Exception):
            self._metrics.counter(
                "tool_runs_total", labels={"tool": "research_and_brief_multi", "outcome": "success"}
            ).inc()
        if offline_sr.status == "uncertain":
            return StepResult.uncertain(data=data)
        return StepResult.ok(data=data)


__all__ = ["ResearchAndBriefMultiTool"]
