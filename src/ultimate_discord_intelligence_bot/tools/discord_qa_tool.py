"""Discord-facing Q&A tool built on the internal vector search abstraction.

Provides a minimal typed interface that returns a list of snippet strings
retrieved via semantic similarity from Qdrant. This wraps :class:`VectorSearchTool`
and intentionally keeps aggregation logic trivial; downstream formatting /
reasoning happens in higher-level agents.
"""

from __future__ import annotations

from typing import TypedDict

from ultimate_discord_intelligence_bot.obs.metrics import get_metrics
from ultimate_discord_intelligence_bot.step_result import StepResult

from ._base import BaseTool
from .vector_search_tool import VectorSearchTool


class _DiscordQAResult(TypedDict, total=False):
    status: str
    snippets: list[str]
    error: str


class DiscordQATool(BaseTool[StepResult]):
    """Expose simple question-answering over stored memory."""

    name: str = "Discord QA Tool"
    description: str = "Answer questions using the vector database."

    # Properly declare field for pydantic v2
    search: VectorSearchTool | None = None

    def __init__(self, search_tool: VectorSearchTool | None = None) -> None:
        super().__init__()
        self.search = search_tool or VectorSearchTool()
        self._metrics = get_metrics()

    def _run(self, question: str, limit: int = 3) -> StepResult:
        if not question or not question.strip():
            self._metrics.counter("tool_runs_total", labels={"tool": "discord_qa", "outcome": "skipped"}).inc()
            return StepResult.ok(skipped=True, reason="empty question", data={"snippets": []})
        if self.search is None:  # pragma: no cover - defensive
            self._metrics.counter("tool_runs_total", labels={"tool": "discord_qa", "outcome": "error"}).inc()
            return StepResult.fail(error="search tool not initialised")
        search_res = self.search.run(question, limit=limit)
        hits: list[dict[str, object]] = []
        if isinstance(search_res, StepResult):
            if not search_res.success:
                self._metrics.counter("tool_runs_total", labels={"tool": "discord_qa", "outcome": "error"}).inc()
                return StepResult.fail(error=search_res.error or "vector search failed")
            hits = search_res.data.get("hits", []) or []
        else:  # pragma: no cover - legacy path
            hits = search_res  # type: ignore[assignment]
        snippets = [str(h.get("text")) for h in hits if isinstance(h, dict) and isinstance(h.get("text"), str)]
        self._metrics.counter("tool_runs_total", labels={"tool": "discord_qa", "outcome": "success"}).inc()
        return StepResult.ok(data={"snippets": snippets})

    def run(self, question: str, limit: int = 3) -> StepResult:  # pragma: no cover - thin wrapper
        try:
            return self._run(question, limit=limit)
        except Exception as exc:  # pragma: no cover - unexpected
            self._metrics.counter("tool_runs_total", labels={"tool": "discord_qa", "outcome": "error"}).inc()
            return StepResult.fail(error=str(exc))
