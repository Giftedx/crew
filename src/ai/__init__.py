"""Compatibility shim for ai package."""

# Re-export routing for backward compatibility
from platform.llm import routing


__all__ = ["routing"]
