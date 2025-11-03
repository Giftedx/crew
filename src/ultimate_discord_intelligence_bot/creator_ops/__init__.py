"""
Creator Operations Multi-Agent System

This module provides comprehensive creator operations capabilities including:
- Multi-platform content ingestion (YouTube, Twitch, TikTok, Instagram, X)
- Advanced media processing (ASR, diarization, NLP, embeddings)
- Creator-facing features (Clip Radar, Repurposing Studio, Intelligence Pack)
- Unified knowledge layer with cross-platform retrieval

The system is designed to help creators like H3 Podcast and Hasan Piker
optimize their content workflows, expand reach, and reduce operational risk.
"""

from __future__ import annotations


__version__ = "1.0.0"
__all__ = ["CreatorOpsConfig", "CreatorOpsError", "enable_creator_ops"]
import os
from platform.core.step_result import StepResult


class CreatorOpsError(Exception):
    """Base exception for Creator Operations errors."""

    def __init__(self, message: str, error_code: str | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.error_code = error_code


class CreatorOpsConfig:
    """Configuration manager for Creator Operations features."""

    def __init__(self) -> None:
        self.enabled = os.getenv("ENABLE_CREATOR_OPS", "false").lower() == "true"
        self.real_apis = os.getenv("ENABLE_REAL_APIS", "false").lower() == "true"
        self.fixture_mode = not self.real_apis

    def validate(self) -> StepResult:
        """Validate Creator Operations configuration."""
        try:
            if not self.enabled:
                return StepResult.ok(data={"status": "disabled"})
            if self.real_apis:
                required_vars = [
                    "YOUTUBE_API_KEY",
                    "TWITCH_CLIENT_ID",
                    "TIKTOK_CLIENT_KEY",
                    "INSTAGRAM_ACCESS_TOKEN",
                    "X_API_KEY",
                ]
                missing = [var for var in required_vars if not os.getenv(var)]
                if missing:
                    return StepResult.fail(f"Missing required API credentials: {', '.join(missing)}")
            return StepResult.ok(data={"status": "valid"})
        except Exception as e:
            return StepResult.fail(f"Configuration validation failed: {e!s}")


def enable_creator_ops() -> bool:
    """Check if Creator Operations is enabled."""
    return CreatorOpsConfig().enabled


config = CreatorOpsConfig()
