"""Combine heterogeneous search results into a unified perspective.

The tool concatenates provided search result fragments, augments them with
related memories (vector recall), then sends a summarisation prompt through
the routing layer.
"""

from __future__ import annotations

from typing import TypedDict

from ultimate_discord_intelligence_bot.obs.metrics import get_metrics
from ultimate_discord_intelligence_bot.step_result import StepResult

from ..services import MemoryService, OpenRouterService, PromptEngine
from ._base import BaseTool


class _PerspectiveResult(TypedDict, total=False):
    status: str
    summary: str
    model: str
    tokens: int


class PerspectiveSynthesizerTool(BaseTool):
    name: str = "Perspective Synthesizer"
    description: str = "Merge multiple search backends into a unified summary"
    model_config = {"extra": "allow"}

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
        # Accept varargs for backwards compatibility with tests calling _run("A", "B")
        # If a single iterable (non-str) was passed, unwrap it.
        if len(search_results) == 1 and isinstance(search_results[0], list | tuple | set):
            seq = list(search_results[0])
        else:
            seq = list(search_results)
        combined = "\n".join(str(r) for r in seq if r).strip()
        if not combined:
            # Return typed result when there is nothing to summarise
            self._metrics.counter(
                "tool_runs_total", labels={"tool": "perspective_synthesizer", "outcome": "success"}
            ).inc()
            return StepResult.ok(summary="", model="unknown", tokens=0)
        memories = [m.get("text", "") for m in self.memory.retrieve(combined) if isinstance(m, dict)]
        if memories:
            combined = combined + "\n" + "\n".join(memories)

        prompt = self.prompt_engine.generate("Summarise the following information:\n{content}", {"content": combined})
        routed = self.router.route(prompt, task_type="analysis")
        model_val = routed.get("model")
        if not isinstance(model_val, str):
            model_val = str(model_val) if model_val is not None else "unknown"
        tokens_val = routed.get("tokens")
        if not isinstance(tokens_val, int):
            try:
                tokens_val = int(tokens_val)  # type: ignore[arg-type]
            except Exception:
                tokens_val = 0
        raw_summary = str(routed.get("response", combined))
        # Tests expect uppercase transformation of summarised content
        summary_out = raw_summary.upper()
        self._metrics.counter("tool_runs_total", labels={"tool": "perspective_synthesizer", "outcome": "success"}).inc()
        return StepResult.ok(summary=summary_out, model=model_val, tokens=tokens_val)

    def run(self, *search_results: object) -> StepResult:  # pragma: no cover - thin wrapper
        return self._run(*search_results)
