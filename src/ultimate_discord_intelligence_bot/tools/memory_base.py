"""Base class for memory tools."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any

from ultimate_discord_intelligence_bot.tools._base import BaseTool


if TYPE_CHECKING:
    from platform.core.step_result import StepResult


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
        return not len(query.strip()) < 3

    def get_memory_metadata(self, query: str) -> dict[str, Any]:
        """Get metadata for memory operations."""
        return {
            "query_length": len(query),
            "memory_types": self.memory_types,
            "max_retrieval_count": self.max_retrieval_count,
            "similarity_threshold": self.similarity_threshold,
        }
