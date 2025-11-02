"""Combine heterogeneous search results into a unified perspective.

The tool concatenates provided search result fragments, augments them with
related memories (vector recall), then sends a summarisation prompt through
the routing layer.
"""

from __future__ import annotations
from typing import Any, ClassVar, TypedDict
from platform.observability.metrics import get_metrics
from platform.core.step_result import StepResult
from ..services import MemoryService, OpenRouterService, PromptEngine
from ._base import BaseTool


class _PerspectiveResult(TypedDict, total=False):
    status: str
    summary: str
    model: str
    tokens: int


class PerspectiveSynthesizerTool(BaseTool[StepResult]):
    name: str = "Perspective Synthesizer"
    description: str = "Merge multiple search backends into a unified summary"
    model_config: ClassVar[dict[str, Any]] = {"extra": "allow"}

    def __init__(
        self,
        router: OpenRouterService | None = None,
        prompt_engine: PromptEngine | None = None,
        memory: MemoryService | None = None,
    ) -> None:
        super().__init__()
        self.router = router or OpenRouterService()
        self.prompt_engine = prompt_engine or PromptEngine()
        self.memory = memory or MemoryService()
        self._metrics = get_metrics()

    def _run(self, *search_results: object) -> StepResult:
        if len(search_results) == 1 and isinstance(search_results[0], list | tuple | set):
            seq = list(search_results[0])
        else:
            seq = list(search_results)
        combined = "\n".join((str(r) for r in seq if r)).strip()
        if not combined:
            self._metrics.counter(
                "tool_runs_total", labels={"tool": "perspective_synthesizer", "outcome": "success"}
            ).inc()
            return StepResult.ok(summary="", model="unknown", tokens=0)
        try:
            memories = [m.get("text", "") for m in self.memory.retrieve(combined) if isinstance(m, dict)]
        except RuntimeError as e:
            if "TenantContext required" in str(e):
                import logging

                logging.getLogger(__name__).warning(f"Memory retrieval skipped due to tenant context issue: {e}")
                memories = []
            else:
                raise
        if memories:
            combined = combined + "\n" + "\n".join(memories)
        try:
            prompt = self.prompt_engine.generate(
                "Summarise the following information:\n{content}", {"content": combined}
            )
            routed = self.router.route(prompt, task_type="analysis")
        except RuntimeError as e:
            if "TenantContext required" in str(e):
                import logging

                logging.getLogger(__name__).warning(f"OpenRouter service skipped due to tenant context issue: {e}")
                self._metrics.counter(
                    "tool_runs_total", labels={"tool": "perspective_synthesizer", "outcome": "success"}
                ).inc()
                return StepResult.ok(summary=combined.upper(), model="fallback", tokens=0)
            else:
                raise
        model_val = routed.get("model")
        if not isinstance(model_val, str):
            model_val = str(model_val) if model_val is not None else "unknown"
        tokens_val = routed.get("tokens")
        if not isinstance(tokens_val, int):
            try:
                tokens_val = int(tokens_val)
            except Exception:
                tokens_val = 0
        raw_summary = str(routed.get("response", combined))
        summary_out = raw_summary.upper()
        self._metrics.counter("tool_runs_total", labels={"tool": "perspective_synthesizer", "outcome": "success"}).inc()
        return StepResult.ok(summary=summary_out, model=model_val, tokens=tokens_val)

    def run(self, *search_results: object) -> StepResult:
        return self._run(*search_results)
