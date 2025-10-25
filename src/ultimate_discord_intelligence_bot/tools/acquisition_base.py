"""Base class for content acquisition tools."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any

from ultimate_discord_intelligence_bot.tools._base import BaseTool


if TYPE_CHECKING:
    from ultimate_discord_intelligence_bot.step_result import StepResult


class AcquisitionBaseTool(BaseTool, ABC):
    """Base class for content acquisition tools."""

    def __init__(self, **kwargs: Any) -> None:
        """Initialize acquisition tool."""
        super().__init__(**kwargs)
        self.supported_platforms: list[str] = []
        self.max_file_size: int = 100 * 1024 * 1024  # 100MB
        self.supported_formats: list[str] = []

    @abstractmethod
    def _run(self, url: str, tenant: str, workspace: str, **kwargs: Any) -> StepResult:
        """Acquire content from URL."""

    def validate_url(self, url: str) -> bool:
        """Validate URL format and platform support."""
        if not url or not isinstance(url, str):
            return False

        # Check if URL is supported by this tool
        return any(platform in url.lower() for platform in self.supported_platforms)

    def get_metadata(self, url: str) -> dict[str, Any]:
        """Extract metadata from URL."""
        return {
            "url": url,
            "platform": self._detect_platform(url),
            "supported": self.validate_url(url),
        }

    def _detect_platform(self, url: str) -> str:
        """Detect platform from URL."""
        url_lower = url.lower()
        for platform in self.supported_platforms:
            if platform in url_lower:
                return platform
        return "unknown"
