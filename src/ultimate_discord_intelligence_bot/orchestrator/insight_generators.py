"""Insight generation and recommendation utilities.

This module contains functions that generate insights, recommendations, and strategic
guidance based on analysis results and quality assessments.

Extracted from analytics_calculators.py to improve maintainability and organization.
"""

import logging
from typing import Any

logger = logging.getLogger(__name__)


def generate_autonomous_insights(results: dict[str, Any], logger: Any | None = None) -> list[str]:
    """Generate autonomous insights based on comprehensive analysis results.

    Args:
        results: Complete analysis results dictionary
        logger: Optional logger instance

    Returns:
        List of insight strings with emoji indicators
    """
    insights = []
    try:
        # Deception score insights
        deception_score = results.get("deception_score", {}).get("deception_score", 0.5)
        if deception_score < 0.3:
            insights.append("🟢 Content shows high reliability with minimal deception indicators")
        elif deception_score < 0.7:
            insights.append("🟡 Content shows mixed reliability signals requiring further verification")
        else:
            insights.append("🔴 Content shows significant deception indicators and should be approached with caution")

        # Fact-checking insights
        fact_data = results.get("fact_analysis", {})
        fallacies = fact_data.get("logical_fallacies", {}).get("fallacies_detected", [])
        if fallacies:
            insights.append(f"⚠️ Detected {len(fallacies)} logical fallacies: {', '.join(fallacies[:3])}")

        # Cross-platform intelligence insights
        intel_data = results.get("cross_platform_intel", {})
        if intel_data and intel_data != {}:
            insights.append("🌐 Cross-platform intelligence gathered from multiple sources")

        # Knowledge base integration insights
        knowledge_data = results.get("knowledge_integration", {})
        if knowledge_data.get("knowledge_storage"):
            insights.append("💾 Analysis results successfully integrated into knowledge base for future reference")

        return insights
    except Exception as e:
        return [f"❌ Insight generation failed: {e}"]


def generate_specialized_insights(results: dict[str, Any], logger: Any | None = None) -> list[str]:
    """Generate specialized insights from comprehensive autonomous analysis.

    Args:
        results: Comprehensive analysis results dictionary
        logger: Optional logger instance

    Returns:
        List of specialized insight strings
    """
    insights = []
    try:
        # Threat assessment insights
        deception_data = results.get("deception", {})
        threat_level = deception_data.get("threat_level", "unknown")

        if threat_level == "low":
            insights.append("🟢 Specialized threat analysis indicates low deception risk with high content reliability")
        elif threat_level == "medium":
            insights.append("🟡 Specialized analysis detected mixed reliability signals requiring verification")
        elif threat_level == "high":
            insights.append("🔴 Specialized threat analysis indicates high deception risk - exercise caution")

        # Verification insights
        verification_data = results.get("verification", {})
        logical_analysis = verification_data.get("logical_analysis", {})
        fallacies = logical_analysis.get("fallacies_detected", [])
        if fallacies:
            insights.append(f"⚠️ Information Verification Specialist detected {len(fallacies)} logical fallacies")

        # Knowledge integration insights
        knowledge_data = results.get("knowledge", {})
        if knowledge_data.get("knowledge_systems"):
            insights.append(
                "💾 Knowledge Integration Manager successfully stored intelligence across all memory systems"
            )

        # Behavioral insights
        behavioral_data = results.get("behavioral", {})
        if behavioral_data.get("behavioral_indicators"):
            consistency = behavioral_data.get("behavioral_indicators", {}).get("consistency_score", 0.5)
            if consistency > 0.7:
                insights.append("📊 Behavioral Pattern Analyst found high consistency indicators")
            elif consistency < 0.3:
                insights.append("⚠️ Behavioral Pattern Analyst detected consistency anomalies")

        # Social intelligence insights
        social_data = results.get("social", {})
        if social_data and social_data != {}:
            insights.append("🌐 Social Intelligence Coordinator gathered cross-platform context")

        return insights
    except Exception as e:
        return [f"❌ Specialized insight generation encountered an error: {e}"]


def generate_ai_recommendations(
    quality_dimensions: dict[str, float],
    ai_quality_score: float,
    analysis_data: dict[str, Any],
    verification_data: dict[str, Any],
    logger: Any | None = None,
) -> list[str]:
    """Produce targeted recommendations based on low-scoring dimensions.

    Args:
        quality_dimensions: Quality dimension scores dictionary
        ai_quality_score: Overall AI quality score
        analysis_data: Analysis results data
        verification_data: Verification results data
        logger: Optional logger instance

    Returns:
        List of actionable recommendations
    """
    recommendations: list[str] = []
    friendly_labels = {
        "content_coherence": "Improve transcript structuring and segmentation.",
        "factual_accuracy": "Collect additional evidence or re-run fact checks.",
        "source_credibility": "Augment source validation with trusted references.",
        "bias_detection": "Expand bias detection prompts or diversify sources.",
        "emotional_manipulation": "Balance emotional framing with neutral summaries.",
        "logical_consistency": "Address detected fallacies with clarifying evidence.",
    }

    for dimension, value in quality_dimensions.items():
        if not isinstance(value, (int, float)):
            continue
        if value < 0.4:
            recommendations.append(f"⚠️ {friendly_labels.get(dimension, dimension)} (score {value:.2f})")
        elif value < 0.6:
            recommendations.append(f"🔍 Monitor {dimension.replace('_', ' ')} (score {value:.2f})")

    if ai_quality_score >= 0.8:
        title = None
        if isinstance(analysis_data, dict):
            metadata = analysis_data.get("content_metadata")
            if isinstance(metadata, dict):
                title = metadata.get("title")
        if title:
            recommendations.append(f"✅ Maintain current quality controls for '{title}'.")
        else:
            recommendations.append("✅ Maintain current quality controls; overall quality is strong.")

    if not recommendations:
        if isinstance(verification_data, dict) and verification_data.get("fact_checks"):
            recommendations.append("✅ Verification coverage is comprehensive; keep existing workflow.")
        else:
            recommendations.append("ℹ️ Add more fact-checking coverage to reinforce confidence.")

    return recommendations


def generate_strategic_recommendations(
    analysis_data: dict[str, Any],
    threat_data: dict[str, Any],
    verification_data: dict[str, Any],
    logger: Any | None = None,
) -> list[str]:
    """Generate strategic recommendations based on analysis.

    Args:
        analysis_data: Analysis results data
        threat_data: Threat assessment data
        verification_data: Verification results data
        logger: Optional logger instance

    Returns:
        List of strategic recommendations
    """
    try:
        recommendations = []
        threat_level = threat_data.get("threat_level", "unknown")

        if threat_level == "high":
            recommendations.append("Recommend enhanced scrutiny and additional verification")
        elif threat_level == "medium":
            recommendations.append("Suggest moderate caution and cross-referencing")
        else:
            recommendations.append("Standard content handling protocols apply")

        return recommendations
    except Exception:
        return ["Strategic recommendation generation encountered an error"]
