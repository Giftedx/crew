"""OpenAI Moderation API integration for content safety screening."""

from __future__ import annotations

import logging
from dataclasses import dataclass


try:
    from openai import OpenAI

    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    OpenAI = None  # type: ignore[assignment,misc]

logger = logging.getLogger(__name__)


@dataclass
class ModerationResult:
    """Result from OpenAI moderation check."""

    flagged: bool
    categories: dict[str, bool]
    category_scores: dict[str, float]
    action: str  # "allow", "block", "review"


class OpenAIModerationService:
    """Service for content moderation using OpenAI Moderation API."""

    def __init__(self, api_key: str | None = None):
        """Initialize OpenAI moderation service.

        Args:
            api_key: OpenAI API key (defaults to OPENAI_API_KEY env var)
        """
        if not OPENAI_AVAILABLE:
            logger.warning("OpenAI not available, moderation disabled")
            self.client = None
            return

        import os

        api_key = api_key or os.getenv("OPENAI_API_KEY")

        if not api_key:
            logger.warning("No OpenAI API key provided, moderation disabled")
            self.client = None
            return

        self.client = OpenAI(api_key=api_key)

    def check_content(self, text: str) -> ModerationResult:
        """Check content against OpenAI moderation API.

        Args:
            text: Text content to check

        Returns:
            ModerationResult with flagged status and categories
        """
        if not self.client:
            # Fallback: allow content if moderation unavailable
            return ModerationResult(flagged=False, categories={}, category_scores={}, action="allow")

        try:
            response = self.client.moderations.create(input=text)
            result = response.results[0]

            # Determine action based on flagged status
            action = "block" if result.flagged else "allow"

            return ModerationResult(
                flagged=result.flagged,
                categories={
                    "hate": result.categories.hate,
                    "hate/threatening": result.categories.hate_threatening,
                    "self-harm": result.categories.self_harm,
                    "sexual": result.categories.sexual,
                    "sexual/minors": result.categories.sexual_minors,
                    "violence": result.categories.violence,
                    "violence/graphic": result.categories.violence_graphic,
                },
                category_scores={
                    "hate": result.category_scores.hate,
                    "hate/threatening": result.category_scores.hate_threatening,
                    "self-harm": result.category_scores.self_harm,
                    "sexual": result.category_scores.sexual,
                    "sexual/minors": result.category_scores.sexual_minors,
                    "violence": result.category_scores.violence,
                    "violence/graphic": result.category_scores.violence_graphic,
                },
                action=action,
            )

        except Exception as e:
            logger.error(f"OpenAI moderation check failed: {e}")
            # Fallback: allow content on API failure
            return ModerationResult(flagged=False, categories={}, category_scores={}, action="allow")

    def check_batch(self, texts: list[str]) -> list[ModerationResult]:
        """Check multiple texts against OpenAI moderation API.

        Args:
            texts: List of text content to check

        Returns:
            List of ModerationResult objects
        """
        if not self.client:
            # Fallback: allow all content
            return [ModerationResult(flagged=False, categories={}, category_scores={}, action="allow") for _ in texts]

        try:
            response = self.client.moderations.create(input=texts)

            results = []
            for result in response.results:
                action = "block" if result.flagged else "allow"

                results.append(
                    ModerationResult(
                        flagged=result.flagged,
                        categories={
                            "hate": result.categories.hate,
                            "hate/threatening": result.categories.hate_threatening,
                            "self-harm": result.categories.self_harm,
                            "sexual": result.categories.sexual,
                            "sexual/minors": result.categories.sexual_minors,
                            "violence": result.categories.violence,
                            "violence/graphic": result.categories.violence_graphic,
                        },
                        category_scores={
                            "hate": result.category_scores.hate,
                            "hate/threatening": result.category_scores.hate_threatening,
                            "self-harm": result.category_scores.self_harm,
                            "sexual": result.category_scores.sexual,
                            "sexual/minors": result.category_scores.sexual_minors,
                            "violence": result.category_scores.violence,
                            "violence/graphic": result.category_scores.violence_graphic,
                        },
                        action=action,
                    )
                )

            return results

        except Exception as e:
            logger.error(f"OpenAI batch moderation check failed: {e}")
            # Fallback: allow all content
            return [ModerationResult(flagged=False, categories={}, category_scores={}, action="allow") for _ in texts]
