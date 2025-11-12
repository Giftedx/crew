"""Compatibility shim for platform.llm.providers.openrouter.quality imports.

Re-exports quality module from openrouter_service subdirectory.
"""

# Re-export quality functions for backward compatibility
from platform.llm.providers.openrouter.openrouter_service.quality import (
    basic_quality_assessment,
    quality_assessment,
    quality_ensemble_assessment,
)


__all__ = [
    "basic_quality_assessment",
    "quality_assessment",
    "quality_ensemble_assessment",
]
