"""Learning and enhancement assessment functions for analysis pipeline.

This module provides functions for identifying learning opportunities and generating
enhancement suggestions based on quality analysis results.
"""

from typing import Any


def identify_learning_opportunities(
    analysis_data: dict[str, Any],
    verification_data: dict[str, Any],
    fact_data: dict[str, Any] | None = None,
) -> list[str]:
    """Highlight opportunities for future workflow improvements.

    Args:
        analysis_data: Analysis data containing transcript index, timeline anchors
        verification_data: Verification data with fact checks and bias indicators
        fact_data: Optional fact checking data (fallback source for fact_checks)

    Returns:
        List of actionable improvement opportunities
    """
    opportunities: list[str] = []

    transcript_index = analysis_data.get("transcript_index") if isinstance(analysis_data, dict) else {}
    if not transcript_index:
        opportunities.append("Generate a transcript index to accelerate follow-up investigations.")

    if isinstance(analysis_data, dict) and not analysis_data.get("timeline_anchors"):
        opportunities.append("Add timeline anchors to support multi-agent temporal reasoning.")

    fact_checks = None
    if isinstance(verification_data, dict):
        fact_checks = verification_data.get("fact_checks")
    if fact_checks is None and isinstance(fact_data, dict):
        fact_checks = fact_data.get("fact_checks")
    if not fact_checks:
        opportunities.append("Expand fact-check coverage to strengthen factual accuracy metrics.")

    bias_indicators = verification_data.get("bias_indicators") if isinstance(verification_data, dict) else None
    if bias_indicators:
        opportunities.append("Review detected bias indicators and adjust sourcing diversity.")

    if not opportunities:
        opportunities.append("Capture analyst retrospectives to preserve implicit learnings.")

    return opportunities


def generate_enhancement_suggestions(
    quality_dimensions: dict[str, float],
    analysis_data: dict[str, Any],
    verification_data: dict[str, Any],
) -> dict[str, Any]:
    """Convert dimension scores into actionable follow-up items.

    Args:
        quality_dimensions: Quality dimension scores (0.0-1.0)
        analysis_data: Analysis data with content metadata
        verification_data: Verification data with source validation

    Returns:
        Dictionary with priority_actions, watch_items, and context
    """
    priority_actions: list[str] = []
    watch_items: list[str] = []

    for dimension, value in quality_dimensions.items():
        if not isinstance(value, (int, float)):
            continue
        label = dimension.replace("_", " ").title()
        if value < 0.4:
            priority_actions.append(f"{label}: urgent remediation required (score {value:.2f}).")
        elif value < 0.6:
            watch_items.append(f"{label}: monitor for drift (score {value:.2f}).")

    if not priority_actions and not watch_items and quality_dimensions:
        priority_actions.append("All quality metrics above targets – maintain current strategy.")

    metadata = analysis_data.get("content_metadata", {}) if isinstance(analysis_data, dict) else {}
    source_validation = verification_data.get("source_validation", {}) if isinstance(verification_data, dict) else {}

    return {
        "priority_actions": priority_actions,
        "watch_items": watch_items,
        "context": {
            "title": metadata.get("title") if metadata else None,
            "platform": metadata.get("platform") if metadata else None,
            "validated_sources": bool(source_validation),
        },
    }
