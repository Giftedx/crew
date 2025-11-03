"""Quality assessment functions for content analysis.

This module provides functions for assessing quality, coherence, accuracy,
credibility, bias, and other quality metrics across analysis outputs.

NOTE: This file has been decomposed into focused modules:
- quality_validators.py - Validation functions for quality assessment
- content_quality_assessors.py - Content coherence and transcript quality assessment
- accuracy_assessors.py - Factual accuracy and source credibility assessment
- bias_manipulation_assessors.py - Bias detection and manipulation assessment
- quality_calculators.py - Overall quality metrics and trend calculations
- learning_enhancement_assessors.py - Learning opportunities and enhancement suggestions

This file is maintained for backward compatibility.
"""

import logging

# ============================================================================
# Backward Compatibility Imports
# ============================================================================
# Import functions from the new focused modules for backward compatibility
from .accuracy_assessors import (
    assess_factual_accuracy,
    assess_source_credibility,
    clamp_score,
)
from .bias_manipulation_assessors import (
    assess_bias_levels,
    assess_emotional_manipulation,
    assess_logical_consistency,
)
from .content_quality_assessors import (
    assess_content_coherence,
    assess_transcript_quality,
)
from .learning_enhancement_assessors import (
    generate_enhancement_suggestions,
    identify_learning_opportunities,
)
from .quality_calculators import (
    assess_quality_trend,
    calculate_overall_confidence,
)
from .quality_validators import (
    detect_placeholder_responses,
    validate_stage_data,
)


logger = logging.getLogger(__name__)

# Export all functions for backward compatibility
__all__ = [
    # Bias manipulation assessors
    "assess_bias_levels",
    # Content quality assessors
    "assess_content_coherence",
    "assess_emotional_manipulation",
    "assess_factual_accuracy",
    "assess_logical_consistency",
    # Quality calculators
    "assess_quality_trend",
    "assess_source_credibility",
    "assess_transcript_quality",
    "calculate_overall_confidence",
    # Accuracy assessors
    "clamp_score",
    # Quality validators
    "detect_placeholder_responses",
    "generate_enhancement_suggestions",
    # Learning enhancement assessors
    "identify_learning_opportunities",
    "validate_stage_data",
]
