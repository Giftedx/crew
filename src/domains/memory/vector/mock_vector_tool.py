"""Mock vector search tool that works without Qdrant.

Migrated to StepResult. Returns StepResult.ok with data results.
Metrics: tool_runs_total{tool="mock_vector_search", outcome}
"""

from typing import Any

from ultimate_discord_intelligence_bot.obs.metrics import get_metrics
from ultimate_discord_intelligence_bot.step_result import StepResult

from ._base import BaseTool


class MockVectorSearchTool(BaseTool[StepResult]):
    """Mock vector search that works without external dependencies."""

    name: str = "Mock Vector Search Tool"
    description: str = "Search stored content using mock vector similarity"

    def __init__(self) -> None:
        super().__init__()
        self.knowledge_base: list[dict[str, Any]] = [
            {
                "text": "The Earth is approximately spherical, supported by scientific evidence.",
                "topic": "geography",
                "confidence": 0.99,
            },
            {
                "text": "Vaccines do not cause autism according to extensive medical research.",
                "topic": "health",
                "confidence": 0.99,
            },
            {
                "text": "Climate change is supported by overwhelming scientific consensus.",
                "topic": "environment",
                "confidence": 0.97,
            },
            {
                "text": "Logical fallacies weaken arguments by introducing flawed reasoning.",
                "topic": "logic",
                "confidence": 0.95,
            },
        ]
        self._metrics = get_metrics()

    def _run(self, query: str, top_k: int = 3) -> StepResult:
        """Perform mock vector search returning StepResult."""
        query_lower = query.lower()
        results: list[dict[str, Any]] = []
        for item in self.knowledge_base:
            score = 0
            text_lower = str(item["text"]).lower()
            query_words = set(query_lower.split())
            text_words = set(text_lower.split())
            matching_words = query_words.intersection(text_words)
            score = len(matching_words)
            if score > 0:
                results.append(
                    {
                        "text": item["text"],
                        "topic": item["topic"],
                        "confidence": item["confidence"],
                        "similarity_score": score,
                    }
                )
        results.sort(key=lambda x: int(x["similarity_score"]), reverse=True)
        data = {
            "query": query,
            "results": results[:top_k],
            "total_found": len(results),
            "note": "Mock vector search - install Qdrant for full semantic search",
        }
        self._metrics.counter("tool_runs_total", labels={"tool": "mock_vector_search", "outcome": "success"}).inc()
        return StepResult.ok(data=data)

    def run(self, query: str, top_k: int = 3) -> StepResult:
        return self._run(query, top_k)
