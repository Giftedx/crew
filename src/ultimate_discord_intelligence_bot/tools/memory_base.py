"""Base class for memory tools."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from ultimate_discord_intelligence_bot.step_result import StepResult
from ultimate_discord_intelligence_bot.tools._base import BaseTool


class MemoryBaseTool(BaseTool, ABC):
    """Base class for memory tools."""

    def __init__(self, **kwargs: Any) -> None:
        """Initialize memory tool."""
        super().__init__(**kwargs)
        self.memory_types: list[str] = []
        self.max_retrieval_count: int = 10
        self.similarity_threshold: float = 0.8

    @abstractmethod
    def _run(self, query: str, tenant: str, workspace: str, **kwargs: Any) -> StepResult:
        """Process memory operation."""

    def validate_query(self, query: str) -> bool:
        """Validate query for memory operations."""
        if not query or not isinstance(query, str):
            return False

        if len(query.strip()) < 3:
            return False

        return True

    def get_memory_metadata(self, query: str) -> dict[str, Any]:
        """Get metadata for memory operations."""
        return {
            "query_length": len(query),
            "memory_types": self.memory_types,
            "max_retrieval_count": self.max_retrieval_count,
            "similarity_threshold": self.similarity_threshold,
        }
