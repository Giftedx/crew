"""Discord-facing Q&A commands using vector search."""

from __future__ import annotations

from crewai.tools import BaseTool

from .vector_search_tool import VectorSearchTool


class DiscordQATool(BaseTool):
    """Expose simple question-answering over stored memory."""

    name: str = "Discord QA Tool"
    description: str = "Answer questions using the vector database."

    # Properly declare field for pydantic v2
    search: VectorSearchTool | None = None

    def __init__(self, search_tool: VectorSearchTool | None = None) -> None:
        super().__init__()
        self.search = search_tool or VectorSearchTool()

    def _run(self, question: str, limit: int = 3):
        hits = self.search.run(question, limit=limit)
        snippets = [h.get("text", "") for h in hits]
        return {"status": "success", "snippets": snippets}

    def run(self, *args, **kwargs):  # pragma: no cover - thin wrapper
        return self._run(*args, **kwargs)
