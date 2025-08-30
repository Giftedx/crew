"""Discord-facing Q&A tool built on the internal vector search abstraction.

Provides a minimal typed interface that returns a list of snippet strings
retrieved via semantic similarity from Qdrant. This wraps :class:`VectorSearchTool`
and intentionally keeps aggregation logic trivial; downstream formatting /
reasoning happens in higher-level agents.
"""

from __future__ import annotations

from typing import TypedDict

from ._base import BaseTool
from .vector_search_tool import VectorSearchTool


class _DiscordQAResult(TypedDict, total=False):
    status: str
    snippets: list[str]
    error: str


class DiscordQATool(BaseTool[_DiscordQAResult]):
    """Expose simple question-answering over stored memory."""

    name: str = "Discord QA Tool"
    description: str = "Answer questions using the vector database."

    # Properly declare field for pydantic v2
    search: VectorSearchTool | None = None

    def __init__(self, search_tool: VectorSearchTool | None = None) -> None:
        super().__init__()
        self.search = search_tool or VectorSearchTool()

    def _run(self, question: str, limit: int = 3) -> _DiscordQAResult:
        if self.search is None:  # pragma: no cover - defensive
            return {"status": "error", "snippets": [], "error": "search tool not initialised"}
        result = self.search.run(question, limit=limit)
        # Error convention: list with single dict containing 'error'
        if result and isinstance(result[0], dict) and "error" in result[0]:
            return {"status": "error", "snippets": [], "error": str(result[0].get("error"))}
        snippets = [str(h.get("text")) for h in result if isinstance(h, dict) and isinstance(h.get("text"), str)]
        return {"status": "success", "snippets": snippets}

    def run(self, question: str, limit: int = 3) -> _DiscordQAResult:  # pragma: no cover - thin wrapper
        return self._run(question, limit=limit)
