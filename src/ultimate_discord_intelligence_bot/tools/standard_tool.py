"""Standardized tool base classes for the Ultimate Discord Intelligence Bot.

This module provides consistent base classes for all tools, ensuring
uniform patterns, error handling, and StepResult usage.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from ultimate_discord_intelligence_bot.step_result import ErrorCategory, ErrorContext, StepResult
from ultimate_discord_intelligence_bot.tools._base import BaseTool


class StandardTool(BaseTool, ABC):
    """Base class for all project tools with StepResult pattern.

    This class provides consistent patterns for tool implementation,
    error handling, and result formatting across the entire project.
    """

    def __init__(self, **kwargs: Any) -> None:
        """Initialize the standard tool."""
        super().__init__(**kwargs)
        self._tool_metadata: dict[str, Any] = {}

    @abstractmethod
    def _run(self, *args: Any, **kwargs: Any) -> StepResult:
        """Execute tool logic. Must return StepResult.

        Args:
            *args: Positional arguments
            **kwargs: Keyword arguments

        Returns:
            StepResult with tool execution results
        """

    def _handle_error(
        self, error: Exception, context: str = "", error_category: ErrorCategory | None = None
    ) -> StepResult:
        """Standard error handling with context.

        Args:
            error: The exception that occurred
            context: Additional context about where the error occurred
            error_category: Optional error categorization for observability

        Returns:
            StepResult.fail with error information and metadata
        """
        error_msg = str(error)
        if context:
            error_msg = f"{context}: {error_msg}"
        category = error_category or ErrorCategory.PROCESSING
        return StepResult.fail(
            error_msg,
            error_category=category,
            error_context=ErrorContext(
                operation=context or "tool_execution",
                component=self.name or self.__class__.__name__,
                additional_context={"exception_type": type(error).__name__},
            ),
            metadata={"tool": self.name or self.__class__.__name__, "error_type": type(error).__name__},
        )

    def _validate_inputs(self, **kwargs: Any) -> StepResult | None:
        """Validate tool inputs.

        Args:
            **kwargs: Input parameters to validate

        Returns:
            StepResult.fail if validation fails, None if valid
        """
        return None

    def _preprocess_inputs(self, **kwargs: Any) -> dict[str, Any]:
        """Preprocess inputs before tool execution.

        Args:
            **kwargs: Raw input parameters

        Returns:
            Processed input parameters
        """
        return kwargs

    def _postprocess_results(self, results: Any) -> Any:
        """Postprocess results before returning.

        Args:
            results: Raw tool results

        Returns:
            Processed results
        """
        return results

    def run(self, *args: Any, **kwargs: Any) -> Any:
        """Public interface for tool execution.

        This method handles validation, preprocessing, execution,
        and postprocessing in a consistent manner.

        Args:
            *args: Positional arguments
            **kwargs: Keyword arguments

        Returns:
            Tool execution results
        """
        try:
            validation_result = self._validate_inputs(**kwargs)
            if validation_result is not None:
                return validation_result
            processed_kwargs = self._preprocess_inputs(**kwargs)
            result = self._run(*args, **processed_kwargs)
            if result.success and result.data is not None:
                result.data = self._postprocess_results(result.data)
            return result
        except Exception as e:
            return self._handle_error(e, f"Tool {self.__class__.__name__} execution failed")

    def get_metadata(self) -> dict[str, Any]:
        """Get tool metadata.

        Returns:
            Dictionary containing tool metadata
        """
        return {"name": self.__class__.__name__, "module": self.__class__.__module__, "metadata": self._tool_metadata}

    def set_metadata(self, key: str, value: Any) -> None:
        """Set tool metadata.

        Args:
            key: Metadata key
            value: Metadata value
        """
        self._tool_metadata[key] = value


class AcquisitionTool(StandardTool):
    """Base class for content acquisition tools.

    Provides common functionality for downloading and capturing
    content from various platforms.
    """

    def _validate_url(self, url: str) -> bool:
        """Validate URL format.

        Args:
            url: URL to validate

        Returns:
            True if URL is valid, False otherwise
        """
        if not url or not isinstance(url, str):
            return False
        return url.startswith(("http://", "https://"))

    def _get_platform(self, url: str) -> str:
        """Detect platform from URL.

        Args:
            url: URL to analyze

        Returns:
            Platform name (youtube, twitch, tiktok, etc.)
        """
        url_lower = url.lower()
        if "youtube.com" in url_lower or "youtu.be" in url_lower:
            return "youtube"
        elif "twitch.tv" in url_lower:
            return "twitch"
        elif "tiktok.com" in url_lower:
            return "tiktok"
        elif "twitter.com" in url_lower or "x.com" in url_lower:
            return "twitter"
        elif "instagram.com" in url_lower:
            return "instagram"
        elif "reddit.com" in url_lower:
            return "reddit"
        else:
            return "unknown"

    def _validate_inputs(self, **kwargs: Any) -> StepResult | None:
        """Validate acquisition tool inputs."""
        url = kwargs.get("url")
        if not url:
            return StepResult.fail("URL is required for acquisition tools")
        if not self._validate_url(url):
            return StepResult.fail(f"Invalid URL format: {url}")
        return None


class AnalysisTool(StandardTool):
    """Base class for content analysis tools.

    Provides common functionality for analyzing content,
    extracting insights, and generating reports.
    """

    def _preprocess_content(self, content: str) -> str:
        """Preprocess content for analysis.

        Args:
            content: Raw content to preprocess

        Returns:
            Preprocessed content
        """
        if not content:
            return ""
        content = content.strip()
        import re

        content = re.sub("\\s+", " ", content)
        return content

    def _postprocess_results(self, results: Any) -> Any:
        """Postprocess analysis results.

        Args:
            results: Raw analysis results

        Returns:
            Processed results with consistent format
        """
        if isinstance(results, dict):
            processed = {
                "analysis_type": self.__class__.__name__,
                "timestamp": self._get_timestamp(),
                "results": results,
            }
            return processed
        return results

    def _get_timestamp(self) -> str:
        """Get current timestamp for analysis results."""
        from datetime import datetime, timezone

        return datetime.now(timezone.utc).isoformat()


class MemoryTool(StandardTool):
    """Base class for memory and storage tools.

    Provides common functionality for storing, retrieving,
    and managing knowledge and memories.
    """

    def _validate_memory_inputs(self, content: str, metadata: dict[str, Any] | None = None) -> StepResult | None:
        """Validate memory tool inputs.

        Args:
            content: Content to store/retrieve
            metadata: Optional metadata

        Returns:
            StepResult.fail if validation fails, None if valid
        """
        if not content or not isinstance(content, str):
            return StepResult.fail("Content is required for memory tools")
        if len(content.strip()) == 0:
            return StepResult.fail("Content cannot be empty")
        return None

    def _format_memory_result(self, operation: str, success: bool, data: Any = None) -> dict[str, Any]:
        """Format memory operation results.

        Args:
            operation: Type of memory operation
            success: Whether operation succeeded
            data: Operation data

        Returns:
            Formatted result dictionary
        """
        return {"operation": operation, "success": success, "timestamp": self._get_timestamp(), "data": data}

    def _get_timestamp(self) -> str:
        """Get current timestamp for memory operations."""
        from datetime import datetime, timezone

        return datetime.now(timezone.utc).isoformat()


class VerificationTool(StandardTool):
    """Base class for verification and fact-checking tools.

    Provides common functionality for verifying claims,
    checking facts, and detecting misinformation.
    """

    def _validate_claims(self, claims: list[str]) -> StepResult | None:
        """Validate claims for verification.

        Args:
            claims: List of claims to verify

        Returns:
            StepResult.fail if validation fails, None if valid
        """
        if not claims or not isinstance(claims, list):
            return StepResult.fail("Claims list is required for verification tools")
        if len(claims) == 0:
            return StepResult.fail("Claims list cannot be empty")
        for i, claim in enumerate(claims):
            if not claim or not isinstance(claim, str):
                return StepResult.fail(f"Claim {i} is invalid: {claim}")
            if len(claim.strip()) == 0:
                return StepResult.fail(f"Claim {i} is empty")
        return None

    def _format_verification_result(self, claims: list[str], results: list[dict[str, Any]]) -> dict[str, Any]:
        """Format verification results.

        Args:
            claims: Original claims
            results: Verification results

        Returns:
            Formatted verification result
        """
        return {
            "total_claims": len(claims),
            "verified_claims": len([r for r in results if r.get("verified", False)]),
            "verification_score": self._calculate_verification_score(results),
            "results": results,
            "timestamp": self._get_timestamp(),
        }

    def _calculate_verification_score(self, results: list[dict[str, Any]]) -> float:
        """Calculate overall verification score.

        Args:
            results: Verification results

        Returns:
            Verification score between 0.0 and 1.0
        """
        if not results:
            return 0.0
        verified_count = sum(1 for r in results if r.get("verified", False))
        return verified_count / len(results)

    def _get_timestamp(self) -> str:
        """Get current timestamp for verification results."""
        from datetime import datetime, timezone

        return datetime.now(timezone.utc).isoformat()
