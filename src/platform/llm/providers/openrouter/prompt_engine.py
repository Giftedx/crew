"""Compatibility shim for openrouter prompt_engine import.

Provides a minimal PromptEngine stub for quality assessment.
"""


class PromptEngine:
    """Minimal stub for PromptEngine to avoid heavy dependencies."""

    def count_tokens(self, text: str) -> int:
        """Simple word-based token estimation."""
        return max(1, len((text or "").split()))


__all__ = ["PromptEngine"]
