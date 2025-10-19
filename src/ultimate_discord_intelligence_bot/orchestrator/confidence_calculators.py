"""Confidence and quality calculation utilities.

This module provides backward compatibility imports for confidence calculation functions
that have been moved to focused modules for better organization and maintainability.

Functions are now organized as follows:
- Persona/Agent confidence: persona_confidence_calculators.py
- AI Quality & Enhancement: ai_quality_calculators.py
- Statistical confidence: statistical_confidence_calculators.py
- Content confidence: content_confidence_calculators.py
"""

# Import all functions from the focused modules for backward compatibility
from .ai_quality_calculators import (
    calculate_ai_enhancement_level,
    calculate_ai_quality_score,
    calculate_overall_confidence,
    calculate_synthesis_confidence,
    calculate_synthesis_confidence_from_crew,
)
from .content_confidence_calculators import (
    calculate_analysis_confidence_from_crew,
    calculate_content_coherence,
    calculate_content_completeness,
    calculate_source_reliability,
    calculate_transcript_quality,
    calculate_verification_confidence_from_crew,
)
from .persona_confidence_calculators import (
    calculate_agent_confidence_from_crew,
    calculate_contextual_relevance,
    calculate_persona_confidence,
    calculate_persona_confidence_from_crew,
)
from .statistical_confidence_calculators import (
    calculate_confidence_interval,
    calculate_confidence_score,
    calculate_reliability_score,
    calculate_standard_error,
    calculate_statistical_significance,
)

# Re-export all functions for backward compatibility
__all__ = [
    # Persona/Agent confidence functions
    "calculate_persona_confidence",
    "calculate_persona_confidence_from_crew",
    "calculate_agent_confidence_from_crew",
    "calculate_contextual_relevance",
    # AI Quality functions
    "calculate_ai_quality_score",
    "calculate_ai_enhancement_level",
    "calculate_synthesis_confidence",
    "calculate_synthesis_confidence_from_crew",
    "calculate_overall_confidence",
    # Statistical confidence functions
    "calculate_confidence_interval",
    "calculate_confidence_score",
    "calculate_reliability_score",
    "calculate_standard_error",
    "calculate_statistical_significance",
    # Content confidence functions
    "calculate_transcript_quality",
    "calculate_analysis_confidence_from_crew",
    "calculate_verification_confidence_from_crew",
    "calculate_content_completeness",
    "calculate_content_coherence",
    "calculate_source_reliability",
]
