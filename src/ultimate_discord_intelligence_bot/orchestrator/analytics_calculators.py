"""Analytics and statistical calculation functions for intelligence workflows.

This module provides pure computational functions for:
- Threat and risk scoring
- Confidence and quality metrics
- Summary statistics
- Resource planning
- Insight generation

All functions are stateless and can be used standalone or integrated
into the orchestrator workflow.

NOTE: This file has been decomposed into focused modules:
- threat_risk_analyzers.py - Threat and risk calculations
- confidence_calculators.py - Confidence and quality metrics
- statistical_analyzers.py - Summary statistics and data analysis
- insight_generators.py - Insight and recommendation generation

This file is maintained for backward compatibility.
"""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


# ============================================================================
# Backward Compatibility Imports
# ============================================================================

# Import functions from the new focused modules for backward compatibility
from .confidence_calculators import (
    calculate_agent_confidence_from_crew,
    calculate_ai_enhancement_level,
    calculate_ai_quality_score,
    calculate_analysis_confidence_from_crew,
    calculate_confidence_interval,
    calculate_contextual_relevance,
    calculate_overall_confidence,
    calculate_persona_confidence,
    calculate_persona_confidence_from_crew,
    calculate_synthesis_confidence,
    calculate_synthesis_confidence_from_crew,
    calculate_transcript_quality,
    calculate_verification_confidence_from_crew,
)
from .insight_generators import (
    generate_ai_recommendations,
    generate_autonomous_insights,
    generate_specialized_insights,
    generate_strategic_recommendations,
)
from .statistical_analyzers import (
    calculate_consolidation_metrics_from_crew,
    calculate_data_completeness,
    calculate_enhanced_summary_statistics,
    calculate_summary_statistics,
)
from .threat_risk_analyzers import (
    calculate_basic_threat_from_data,
    calculate_behavioral_risk,
    calculate_behavioral_risk_from_crew,
    calculate_composite_deception_score,
    calculate_comprehensive_threat_score,
    calculate_threat_level,
    calculate_threat_level_from_crew,
)

# Export all functions for backward compatibility
__all__ = [
    # Threat and risk calculations
    "calculate_threat_level",
    "calculate_threat_level_from_crew",
    "calculate_behavioral_risk",
    "calculate_behavioral_risk_from_crew",
    "calculate_composite_deception_score",
    "calculate_comprehensive_threat_score",
    "calculate_basic_threat_from_data",
    # Confidence and quality metrics
    "calculate_persona_confidence",
    "calculate_persona_confidence_from_crew",
    "calculate_agent_confidence_from_crew",
    "calculate_contextual_relevance",
    "calculate_ai_quality_score",
    "calculate_ai_enhancement_level",
    "calculate_confidence_interval",
    "calculate_synthesis_confidence",
    "calculate_synthesis_confidence_from_crew",
    "calculate_overall_confidence",
    "calculate_transcript_quality",
    "calculate_analysis_confidence_from_crew",
    "calculate_verification_confidence_from_crew",
    # Statistical analysis
    "calculate_summary_statistics",
    "calculate_consolidation_metrics_from_crew",
    "calculate_data_completeness",
    "calculate_enhanced_summary_statistics",
    # Insight generation
    "generate_autonomous_insights",
    "generate_specialized_insights",
    "generate_ai_recommendations",
    "generate_strategic_recommendations",
]
