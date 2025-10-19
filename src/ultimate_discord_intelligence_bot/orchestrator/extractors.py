"""Result extraction utilities for CrewAI outputs.

This module contains pure extraction functions that parse CrewAI crew results
into structured data. All functions follow a consistent pattern:
- Accept CrewAI result objects (Any type for flexibility)
- Return typed Python structures (dict, list, float, etc.)
- Handle errors gracefully with try/except and sensible defaults
- Use simple pattern matching and text analysis

NOTE: This file has been decomposed into focused modules:
- content_extractors.py - Content analysis and text processing functions
- fact_checking_extractors.py - Fact-checking and verification functions
- bias_manipulation_extractors.py - Bias detection and manipulation analysis
- confidence_calculators.py - Confidence and quality scoring functions

This file is maintained for backward compatibility.
"""

import logging

logger = logging.getLogger(__name__)


# ============================================================================
# Backward Compatibility Imports
# ============================================================================

# Import functions from the new focused modules for backward compatibility
from .bias_manipulation_extractors import (
    calculate_comprehensive_threat_score_from_crew,
    extract_bias_indicators_from_crew,
    extract_deception_analysis_from_crew,
    extract_manipulation_indicators_from_crew,
    extract_narrative_integrity_from_crew,
    extract_psychological_threats_from_crew,
)
from .confidence_calculators import (
    calculate_agent_confidence_from_crew,
    calculate_analysis_confidence_from_crew,
    calculate_synthesis_confidence_from_crew,
)
from .content_extractors import (
    calculate_transcript_quality,
    extract_index_from_crew,
    extract_keywords_from_text,
    extract_language_features,
    extract_linguistic_patterns_from_crew,
    extract_sentiment_from_crew,
    extract_themes_from_crew,
    extract_timeline_from_crew,
)
from .fact_checking_extractors import (
    calculate_verification_confidence_from_crew,
    extract_credibility_from_crew,
    extract_fact_checks_from_crew,
    extract_logical_analysis_from_crew,
    extract_source_validation_from_crew,
)

# Export all functions for backward compatibility
__all__ = [
    # Content extraction functions
    "extract_timeline_from_crew",
    "extract_index_from_crew",
    "extract_keywords_from_text",
    "extract_linguistic_patterns_from_crew",
    "extract_sentiment_from_crew",
    "extract_themes_from_crew",
    "extract_language_features",
    "calculate_transcript_quality",
    # Fact-checking functions
    "extract_fact_checks_from_crew",
    "extract_logical_analysis_from_crew",
    "extract_credibility_from_crew",
    "extract_source_validation_from_crew",
    "calculate_verification_confidence_from_crew",
    # Bias and manipulation functions
    "extract_bias_indicators_from_crew",
    "extract_deception_analysis_from_crew",
    "extract_manipulation_indicators_from_crew",
    "extract_narrative_integrity_from_crew",
    "extract_psychological_threats_from_crew",
    "calculate_comprehensive_threat_score_from_crew",
    # Confidence calculation functions
    "calculate_agent_confidence_from_crew",
    "calculate_analysis_confidence_from_crew",
    "calculate_synthesis_confidence_from_crew",
]
