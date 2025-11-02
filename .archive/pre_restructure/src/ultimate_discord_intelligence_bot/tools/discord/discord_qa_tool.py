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

from .._base import BaseTool
from ..memory.vector_search_tool import VectorSearchTool


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
        # Enforce non-empty, meaningful questions to avoid agent spam
        import os

        try:
            min_len = int(os.getenv("DISCORD_QA_MIN_LEN", "8").strip())
        except Exception:
            min_len = 8
        if (not question) or (not question.strip()) or (len(question.strip()) < max(1, min_len)):
            self._metrics.counter("tool_runs_total", labels={"tool": "discord_qa", "outcome": "skipped"}).inc()
            return StepResult.skip(reason="empty question", data={"snippets": []})
        if self.search is None:  # pragma: no cover - defensive
            self._metrics.counter("tool_runs_total", labels={"tool": "discord_qa", "outcome": "error"}).inc()
            return StepResult.fail(error="search tool not initialised")
        # Any-typed to avoid narrowing that makes legacy branch appear unreachable to mypy
        search_res: object = self.search.run(question, limit=limit)
        hits: list[dict[str, object]] = []
        if isinstance(search_res, StepResult):
            if not search_res.success:
                self._metrics.counter("tool_runs_total", labels={"tool": "discord_qa", "outcome": "error"}).inc()
                return StepResult.fail(error=search_res.error or "vector search failed")
            hits = search_res.data.get("hits", []) or []
        else:  # pragma: no cover - legacy path
            # Legacy adapters may return a plain list of hit dicts
            if isinstance(search_res, list):
                hits = list(search_res)
        snippets = [str(h.get("text")) for h in hits if isinstance(h, dict) and isinstance(h.get("text"), str)]
        self._metrics.counter("tool_runs_total", labels={"tool": "discord_qa", "outcome": "success"}).inc()
        return StepResult.ok(data={"snippets": snippets})

    def run(self, *args, **kwargs) -> StepResult:  # pragma: no cover - thin wrapper
        try:
            question = ""
            limit = int(kwargs.get("limit", 3))
            if args:
                question = str(args[0])
                if len(args) > 1:
                    try:
                        limit = int(args[1])
                    except Exception:
                        limit = int(kwargs.get("limit", 3))
            else:
                # Accept alias 'query' used by some agents
                question = str(kwargs.get("question", kwargs.get("query", "")))
            import os

            try:
                min_len = int(os.getenv("DISCORD_QA_MIN_LEN", "8").strip())
            except Exception:
                min_len = 8
            if (not question) or (not question.strip()) or (len(question.strip()) < max(1, min_len)):
                self._metrics.counter(
                    "tool_runs_total",
                    labels={"tool": "discord_qa", "outcome": "skipped"},
                ).inc()
                return StepResult.skip(reason="empty question", data={"snippets": []})
            return self._run(question, limit=limit)
        except Exception as exc:  # pragma: no cover - unexpected
            self._metrics.counter("tool_runs_total", labels={"tool": "discord_qa", "outcome": "error"}).inc()
            return StepResult.fail(error=str(exc))
