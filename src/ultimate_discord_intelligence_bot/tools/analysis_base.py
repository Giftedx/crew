"""Base class for content analysis tools."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any

from ultimate_discord_intelligence_bot.tools._base import BaseTool


if TYPE_CHECKING:
    from ultimate_discord_intelligence_bot.step_result import StepResult


class AnalysisBaseTool(BaseTool, ABC):
    """Base class for content analysis tools."""

    def __init__(self, **kwargs: Any) -> None:
        """Initialize analysis tool."""
        super().__init__(**kwargs)
        self.analysis_types: list[str] = []
        self.confidence_threshold: float = 0.7
        self.max_content_length: int = 10000

    @abstractmethod
    def _run(self, content: str, tenant: str, workspace: str, **kwargs: Any) -> StepResult:
        """Analyze content."""

    def validate_content(self, content: str) -> bool:
        """Validate content for analysis."""
        if not content or not isinstance(content, str):
            return False
        return not len(content) > self.max_content_length

    def get_analysis_metadata(self, content: str) -> dict[str, Any]:
        """Get metadata for analysis."""
        return {
            "content_length": len(content),
            "word_count": len(content.split()),
            "analysis_types": self.analysis_types,
            "confidence_threshold": self.confidence_threshold,
        }
