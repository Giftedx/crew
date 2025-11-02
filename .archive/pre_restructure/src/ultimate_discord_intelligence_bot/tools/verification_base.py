"""Base class for verification tools."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any

from ultimate_discord_intelligence_bot.tools._base import BaseTool


if TYPE_CHECKING:
    from ultimate_discord_intelligence_bot.step_result import StepResult


class VerificationBaseTool(BaseTool, ABC):
    """Base class for verification tools."""

    def __init__(self, **kwargs: Any) -> None:
        """Initialize verification tool."""
        super().__init__(**kwargs)
        self.verification_types: list[str] = []
        self.confidence_threshold: float = 0.8
        self.max_claims: int = 50

    @abstractmethod
    def _run(self, content: str, tenant: str, workspace: str, **kwargs: Any) -> StepResult:
        """Verify content."""

    def validate_claims(self, claims: list[str]) -> bool:
        """Validate claims for verification."""
        if not claims or not isinstance(claims, list):
            return False

        if len(claims) > self.max_claims:
            return False

        return all(isinstance(claim, str) and claim.strip() for claim in claims)

    def get_verification_metadata(self, claims: list[str]) -> dict[str, Any]:
        """Get metadata for verification."""
        return {
            "claim_count": len(claims),
            "verification_types": self.verification_types,
            "confidence_threshold": self.confidence_threshold,
            "max_claims": self.max_claims,
        }
