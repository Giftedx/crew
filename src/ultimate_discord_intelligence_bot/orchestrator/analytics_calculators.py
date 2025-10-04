"""Analytics and statistical calculation functions for intelligence workflows.

This module provides pure computational functions for:
- Threat and risk scoring
- Confidence and quality metrics
- Summary statistics
- Resource planning
- Insight generation

All functions are stateless and can be used standalone or integrated
into the orchestrator workflow.

Extracted from autonomous_orchestrator.py as part of Week 3 decomposition.
"""

from __future__ import annotations

import logging
from typing import Any

from ..step_result import StepResult

logger = logging.getLogger(__name__)


# ============================================================================
# Lazy Import Helpers (Avoid Circular Dependencies)
# ============================================================================


def _get_extractors():
    """Lazy import of extractors module to avoid circular dependencies."""
    from . import extractors

    return extractors


# ============================================================================
# Category 1: Threat & Risk Calculations
# ============================================================================


def calculate_threat_level(deception_result: Any, fallacy_result: Any, log: logging.Logger | None = None) -> str:
    """Calculate threat level based on deception and fallacy analysis.

    Args:
        deception_result: StepResult from deception scoring tool
        fallacy_result: StepResult from fallacy detection
        log: Optional logger instance

    Returns:
        Threat level: "high", "medium", "low", or "unknown"
    """
    _logger = log or logger
    try:
        deception_score = 0.0
        fallacy_count = 0

        if isinstance(deception_result, StepResult) and deception_result.success:
            deception_data = deception_result.data
            deception_score = deception_data.get("threat_score", 0.0)

        if isinstance(fallacy_result, StepResult) and fallacy_result.success:
            fallacy_data = fallacy_result.data
            fallacy_count = len(fallacy_data.get("fallacies", []))

        # Calculate combined threat level
        if deception_score > 0.7 or fallacy_count > 5:
            return "high"
        elif deception_score > 0.4 or fallacy_count > 2:
            return "medium"
        else:
            return "low"
    except Exception:
        return "unknown"


def calculate_threat_level_from_crew(crew_result: Any, log: logging.Logger | None = None) -> str:
    """Calculate threat level from CrewAI crew analysis results.

    Args:
        crew_result: Raw crew execution result
        log: Optional logger instance

    Returns:
        Threat level: "high", "medium", "low", or "unknown"
    """
    _logger = log or logger
    try:
        if not crew_result:
            return "unknown"

        # Extract analysis from crew result
        crew_output = str(crew_result).lower()

        # Look for threat indicators in crew output
        high_indicators = ["high risk", "severe threat", "critical", "dangerous", "manipulation", "deception"]
        medium_indicators = ["moderate risk", "medium threat", "concerning", "suspicious", "misleading"]

        high_count = sum(1 for indicator in high_indicators if indicator in crew_output)
        medium_count = sum(1 for indicator in medium_indicators if indicator in crew_output)

        if high_count > 0:
            return "high"
        elif medium_count > 0:
            return "medium"
        else:
            return "low"
    except Exception:
        return "unknown"


def calculate_behavioral_risk(
    behavioral_data: dict[str, Any], threat_data: dict[str, Any], log: logging.Logger | None = None
) -> float:
    """Calculate behavioral risk score.

    Args:
        behavioral_data: Dictionary with behavioral analysis data (perspectives, etc.)
        threat_data: Dictionary with threat level information
        log: Optional logger for diagnostics

    Returns:
        Risk score from 0.0 to 1.0
    """
    _logger = log or logger
    try:
        base_risk = 0.0

        # Factor in threat level
        threat_level = threat_data.get("threat_level", "unknown")
        if threat_level == "high":
            base_risk += 0.4
        elif threat_level == "medium":
            base_risk += 0.2

        # Factor in behavioral patterns
        perspectives = behavioral_data.get("perspectives", {})
        if isinstance(perspectives, dict):
            negative_indicators = sum(1 for p in perspectives.values() if "concerning" in str(p).lower())
            base_risk += min(negative_indicators * 0.1, 0.3)

        return min(base_risk, 1.0)
    except Exception as e:
        _logger.debug(f"Behavioral risk calculation error: {e}")
        return 0.5


def calculate_behavioral_risk_from_crew(
    crew_result: Any, threat_data: dict[str, Any], log: logging.Logger | None = None
) -> float:
    """Calculate behavioral risk score from CrewAI crew analysis.

    Args:
        crew_result: Raw crew analysis result
        threat_data: Dictionary with threat level information
        log: Optional logger for diagnostics

    Returns:
        Risk score from 0.0 to 1.0
    """
    _logger = log or logger
    try:
        base_risk = 0.0

        # Factor in threat level
        threat_level = threat_data.get("threat_level", "unknown")
        if threat_level == "high":
            base_risk += 0.4
        elif threat_level == "medium":
            base_risk += 0.2

        # Analyze crew output for risk indicators
        crew_output = str(crew_result).lower()
        risk_indicators = ["aggressive", "deceptive", "manipulative", "concerning", "suspicious", "high risk"]
        risk_count = sum(1 for indicator in risk_indicators if indicator in crew_output)

        base_risk += min(risk_count * 0.1, 0.4)

        return min(base_risk, 1.0)
    except Exception as e:
        _logger.debug(f"Behavioral risk from crew calculation error: {e}")
        return 0.5


def calculate_persona_confidence(behavioral_data: dict[str, Any], log: logging.Logger | None = None) -> float:
    """Calculate confidence in persona analysis.

    Args:
        behavioral_data: Dictionary with behavioral analysis data (perspectives, etc.)
        log: Optional logger for diagnostics

    Returns:
        Confidence score from 0.0 to 1.0
    """
    _logger = log or logger
    try:
        perspectives = behavioral_data.get("perspectives", {})
        if isinstance(perspectives, dict) and len(perspectives) > 0:
            # Higher confidence with more consistent perspectives
            return min(len(perspectives) * 0.2, 0.9)
        return 0.1
    except Exception as e:
        _logger.debug(f"Persona confidence calculation error: {e}")
        return 0.1


def calculate_persona_confidence_from_crew(crew_result: Any, log: logging.Logger | None = None) -> float:
    """Calculate confidence in persona analysis from CrewAI crew results.

    Args:
        crew_result: Raw crew analysis result
        log: Optional logger for diagnostics

    Returns:
        Confidence score from 0.0 to 1.0
    """
    _logger = log or logger
    try:
        if not crew_result:
            return 0.1

        crew_output = str(crew_result)

        # Higher confidence with more detailed analysis
        confidence_indicators = ["detailed", "comprehensive", "analysis", "profile", "behavior", "pattern"]
        confidence_count = sum(1 for indicator in confidence_indicators if indicator in crew_output.lower())

        # Base confidence on output length and detail indicators
        base_confidence = min(len(crew_output) / 1000, 0.5)  # Length factor
        detail_confidence = min(confidence_count * 0.1, 0.4)  # Detail factor

        return min(base_confidence + detail_confidence, 0.9)
    except Exception as e:
        _logger.debug(f"Persona confidence from crew calculation error: {e}")
        return 0.1


def calculate_composite_deception_score(
    deception_result: Any,
    truth_result: Any,
    trust_result: Any,
    fact_data: dict[str, Any],
    log: logging.Logger | None = None,
) -> float:
    """Calculate composite deception score from multiple analysis sources.

    Args:
        deception_result: Result from deception scoring tool
        truth_result: Truth assessment result
        trust_result: Trust analysis result
        fact_data: Fact-checking data
        log: Optional logger for diagnostics

    Returns:
        Composite deception score from 0.0 to 1.0
    """
    _logger = log or logger
    try:
        # Base score from deception tool
        base_score = 0.5  # neutral
        if isinstance(deception_result, StepResult) and deception_result.success:
            base_score = float(deception_result.data.get("score", 0.5))

        # Factor in fact-check results
        fact_checks = fact_data.get("fact_checks", {})
        if fact_checks:
            verified_claims = fact_checks.get("verified_claims", 0)
            disputed_claims = fact_checks.get("disputed_claims", 0)
            total_claims = verified_claims + disputed_claims
            if total_claims > 0:
                fact_score = disputed_claims / total_claims
                base_score = (base_score * 0.6) + (fact_score * 0.4)

        # Factor in logical fallacies
        fallacies = fact_data.get("logical_fallacies", {}).get("fallacies_detected", [])
        if fallacies:
            fallacy_penalty = min(0.3, len(fallacies) * 0.1)
            base_score = min(1.0, base_score + fallacy_penalty)

        return max(0.0, min(1.0, base_score))
    except Exception as e:
        _logger.debug(f"Composite deception score calculation error: {e}")
        return 0.5


def calculate_comprehensive_threat_score(
    deception_result: Any,
    truth_result: Any,
    trust_result: Any,
    verification_data: dict[str, Any],
    log: logging.Logger | None = None,
) -> float:
    """Calculate comprehensive threat score from multiple analysis sources.

    Args:
        deception_result: Deception analysis result
        truth_result: Truth assessment result
        trust_result: Trust analysis result
        verification_data: Verification and fact-checking data
        log: Optional logger for diagnostics

    Returns:
        Comprehensive threat score from 0.0 to 1.0
    """
    _logger = log or logger
    try:
        threat_score = 0.5  # Base threat level

        # Factor in deception analysis
        if isinstance(deception_result, StepResult) and deception_result.success:
            threat_score = deception_result.data.get("deception_score", 0.5)

        # Factor in verification results (support both 'fact_checks' and legacy 'fact_verification')
        fact_block = None
        if isinstance(verification_data.get("fact_checks"), dict):
            fact_block = verification_data.get("fact_checks", {})
        elif isinstance(verification_data.get("fact_verification"), dict):
            fact_block = verification_data.get("fact_verification", {})
        if isinstance(fact_block, dict) and fact_block:
            verified = fact_block.get("verified_claims")
            disputed = fact_block.get("disputed_claims")
            if isinstance(verified, int) and isinstance(disputed, int) and (verified + disputed) > 0:
                total = verified + disputed
                dispute_ratio = disputed / total
                threat_score = (threat_score * 0.6) + (dispute_ratio * 0.4)
            else:
                # Heuristic when only evidence is present
                ev_ct = fact_block.get("evidence_count")
                if isinstance(ev_ct, int) and ev_ct > 0:
                    threat_score = max(0.0, threat_score - min(0.1, ev_ct * 0.01))

        # Factor in logical fallacies
        logical_analysis = verification_data.get("logical_analysis", {})
        fallacies = logical_analysis.get("fallacies_detected", [])
        if fallacies:
            fallacy_penalty = min(0.3, len(fallacies) * 0.1)
            threat_score = min(1.0, threat_score + fallacy_penalty)

        return max(0.0, min(1.0, threat_score))
    except Exception as e:
        _logger.debug(f"Comprehensive threat score calculation error: {e}")
        return 0.5


def calculate_basic_threat_from_data(
    verification_data: dict[str, Any],
    sentiment_data: dict[str, Any],
    credibility_data: dict[str, Any],
    log: logging.Logger | None = None,
) -> float:
    """Calculate basic threat score from available data when agent unavailable.

    Args:
        verification_data: Verification results
        sentiment_data: Sentiment analysis data
        credibility_data: Credibility assessment data
        log: Optional logger for diagnostics

    Returns:
        Basic threat score from 0.0 to 1.0
    """
    _logger = log or logger
    try:
        base_threat = 0.0

        # Factor in verification results
        fact_checks = verification_data.get("fact_checks", {})
        if isinstance(fact_checks, dict):
            disputed_claims = fact_checks.get("disputed_claims", 0)
            verified_claims = fact_checks.get("verified_claims", 1)
            base_threat += min(disputed_claims / max(verified_claims, 1), 0.4)

        # Factor in sentiment
        if isinstance(sentiment_data, dict):
            sentiment = sentiment_data.get("overall_sentiment", "neutral")
            if sentiment == "negative":
                base_threat += 0.2
            elif sentiment == "positive":
                base_threat -= 0.1

        # Factor in credibility
        if isinstance(credibility_data, dict):
            credibility_score = credibility_data.get("score", 0.5)
            base_threat += (1.0 - credibility_score) * 0.3

        return max(0.0, min(1.0, base_threat))
    except Exception as e:
        _logger.debug(f"Basic threat calculation error: {e}")
        return 0.5


def calculate_agent_confidence_from_crew(crew_result: Any, log: logging.Logger | None = None) -> float:
    """Calculate agent confidence from CrewAI analysis quality.

    Args:
        crew_result: Raw crew analysis result
        log: Optional logger for diagnostics

    Returns:
        Confidence score from 0.0 to 1.0
    """
    _logger = log or logger
    # Delegate to extractors module for consistency
    extractors_module = _get_extractors()
    return extractors_module.calculate_agent_confidence_from_crew(crew_result)


def calculate_contextual_relevance(
    research_results: dict[str, Any], analysis_data: dict[str, Any], log: logging.Logger | None = None
) -> float:
    """Calculate contextual relevance of research to analysis.

    Args:
        research_results: Research findings data
        analysis_data: Analysis results data
        log: Optional logger for diagnostics

    Returns:
        Relevance score from 0.0 to 1.0
    """
    _logger = log or logger
    try:
        if not research_results:
            return 0.0

        # Simple relevance calculation based on result count and quality
        total_results = sum(len(results) for results in research_results.values() if isinstance(results, list))
        return min(total_results * 0.1, 0.9)
    except Exception as e:
        _logger.debug(f"Contextual relevance calculation error: {e}")
        return 0.0


# ============================================================================
# Category 2: Quality & Confidence Metrics
# ============================================================================


def calculate_ai_quality_score(quality_dimensions: dict[str, float], log: logging.Logger | None = None) -> float:
    """Calculate a composite AI quality score from the assessed dimensions.

    Args:
        quality_dimensions: Dictionary of quality dimension names to scores
        log: Optional logger for debugging

    Returns:
        Composite quality score (0.0-1.0)
    """
    _logger = log or logger
    try:
        values = [float(v) for v in quality_dimensions.values() if isinstance(v, (int, float))]
        if not values:
            return 0.0
        score = sum(values) / len(values)
        return max(0.0, min(1.0, round(score, 3)))
    except Exception as exc:
        _logger.debug("AI quality score calculation error: %s", exc)
        return 0.0


def calculate_ai_enhancement_level(depth: str, log: logging.Logger | None = None) -> float:
    """Calculate the level of AI enhancement applied based on analysis depth.

    Args:
        depth: Analysis depth level (standard/deep/comprehensive/experimental)
        log: Optional logger for debugging

    Returns:
        Enhancement level score (0.3-1.0)
    """
    enhancement_levels = {
        "standard": 0.3,
        "deep": 0.6,
        "comprehensive": 0.8,
        "experimental": 1.0,
    }
    return enhancement_levels.get(depth, 0.3)


def calculate_confidence_interval(
    quality_dimensions: dict[str, float], ai_quality_score: float, log: logging.Logger | None = None
) -> dict[str, float]:
    """Provide a simple confidence interval for the composite quality score.

    Args:
        quality_dimensions: Dictionary of quality dimension scores
        ai_quality_score: Overall quality score
        log: Optional logger for debugging

    Returns:
        Dictionary with 'lower', 'upper', and 'confidence' keys
    """
    _logger = log or logger
    try:
        import math
        import statistics

        values = [float(v) for v in quality_dimensions.values() if isinstance(v, (int, float))]
        if not values:
            margin = 0.2
            confidence = 0.5
        elif len(values) == 1:
            margin = 0.1
            confidence = 0.68
        else:
            spread = statistics.pstdev(values)
            margin = max(0.05, spread / math.sqrt(len(values)))
            confidence = 0.9

        # Clamp scores to [0.0, 1.0]
        lower = max(0.0, min(1.0, ai_quality_score - margin))
        upper = max(0.0, min(1.0, ai_quality_score + margin))

        return {"lower": lower, "upper": upper, "confidence": confidence}
    except Exception as exc:
        _logger.debug("Confidence interval calculation fallback due to error: %s", exc)
        # Clamp fallback values
        lower = max(0.0, min(1.0, ai_quality_score - 0.1))
        upper = max(0.0, min(1.0, ai_quality_score + 0.1))
        return {"lower": lower, "upper": upper, "confidence": 0.5}


def calculate_synthesis_confidence(research_results: dict[str, Any], log: logging.Logger | None = None) -> float:
    """Calculate confidence in research synthesis.

    Args:
        research_results: Dictionary of research data
        log: Optional logger for debugging

    Returns:
        Synthesis confidence score (0.0-0.8)
    """
    try:
        if not research_results:
            return 0.0
        return min(len(research_results) * 0.2, 0.8)
    except Exception:
        return 0.0


def calculate_synthesis_confidence_from_crew(crew_result: Any, log: logging.Logger | None = None) -> float:
    """Calculate synthesis confidence from CrewAI crew results.

    Args:
        crew_result: CrewAI crew output
        log: Optional logger for debugging

    Returns:
        Synthesis confidence score (0.0-0.8)
    """
    try:
        if not crew_result:
            return 0.0
        crew_output = str(crew_result)
        # Calculate confidence based on analysis depth and quality indicators
        confidence_indicators = ["comprehensive", "thorough", "detailed", "verified", "confirmed"]
        confidence_count = sum(1 for indicator in confidence_indicators if indicator in crew_output.lower())
        return min(confidence_count * 0.15, 0.8)
    except Exception:
        return 0.0


def calculate_overall_confidence(*data_sources, log: logging.Logger | None = None) -> float:
    """Calculate overall confidence across all data sources.

    Delegates to quality_assessors module.

    Args:
        *data_sources: Variable number of data source dictionaries
        log: Optional logger for debugging

    Returns:
        Overall confidence score (0.0-1.0)
    """
    try:
        # Lazy import to avoid circular dependencies
        from . import quality_assessors

        return quality_assessors.calculate_overall_confidence(*data_sources, logger_instance=log or logger)
    except Exception as exc:
        _logger = log or logger
        _logger.debug("Overall confidence calculation error: %s", exc)
        return 0.0


def calculate_transcript_quality(crew_result: Any, log: logging.Logger | None = None) -> float:
    """Calculate transcript quality from CrewAI analysis.

    Delegates to extractors module.

    Args:
        crew_result: CrewAI crew output
        log: Optional logger for debugging

    Returns:
        Transcript quality score (0.0-1.0)
    """
    try:
        extractors_module = _get_extractors()
        return extractors_module.calculate_transcript_quality(crew_result)
    except Exception as exc:
        _logger = log or logger
        _logger.debug("Transcript quality calculation error: %s", exc)
        return 0.0


def calculate_analysis_confidence_from_crew(crew_result: Any, log: logging.Logger | None = None) -> float:
    """Calculate analysis confidence from CrewAI results.

    Delegates to extractors module.

    Args:
        crew_result: CrewAI crew output
        log: Optional logger for debugging

    Returns:
        Analysis confidence score (0.0-1.0)
    """
    try:
        extractors_module = _get_extractors()
        return extractors_module.calculate_analysis_confidence_from_crew(crew_result)
    except Exception as exc:
        _logger = log or logger
        _logger.debug("Analysis confidence calculation error: %s", exc)
        return 0.0


def calculate_verification_confidence_from_crew(crew_result: Any, log: logging.Logger | None = None) -> float:
    """Calculate overall verification confidence from CrewAI analysis.

    Delegates to extractors module.

    Args:
        crew_result: CrewAI crew output
        log: Optional logger for debugging

    Returns:
        Verification confidence score (0.0-1.0)
    """
    try:
        extractors_module = _get_extractors()
        return extractors_module.calculate_verification_confidence_from_crew(crew_result)
    except Exception as exc:
        _logger = log or logger
        _logger.debug("Verification confidence calculation error: %s", exc)
        return 0.0


# Category 3: Summary & Statistics
# ============================================================================


def calculate_summary_statistics(results: dict[str, Any], log: logging.Logger | None = None) -> dict[str, Any]:
    """Calculate summary statistics from all analysis results.

    Args:
        results: Dictionary containing all analysis results (pipeline, fact_analysis, etc.)
        log: Optional logger for debugging

    Returns:
        Dictionary with summary statistics (content_processed, fact_checks_performed, etc.)
    """
    _logger = log or logger
    try:
        pipeline_data = results.get("pipeline", {})
        fact_data = results.get("fact_analysis", {})

        # Prefer explicit deception_scoring stage, fallback to threat_analysis.deception_score
        deception_stage = results.get("deception_scoring", {})
        if isinstance(deception_stage, dict) and "score" in deception_stage:
            deception_score_val = deception_stage.get("score", 0.0)
        else:
            ta = results.get("threat_analysis", {})
            deception_score_val = ta.get("deception_score", 0.0) if isinstance(ta, dict) else 0.0

        # Derive a more accurate count of fact-checks performed
        fc = fact_data.get("fact_checks", {}) if isinstance(fact_data, dict) else {}
        checks_performed = 0
        if isinstance(fc, dict):
            items = fc.get("items")
            claims = fc.get("claims")
            if isinstance(items, list):
                checks_performed = len(items)
            elif isinstance(claims, list):
                checks_performed = len(claims)
            else:
                # fallback to evidence count if available
                ev_ct = fc.get("evidence_count")
                if isinstance(ev_ct, int):
                    checks_performed = ev_ct

        stats = {
            "content_processed": bool(pipeline_data),
            "fact_checks_performed": checks_performed,
            "fallacies_detected": len(fact_data.get("logical_fallacies", {}).get("fallacies_detected", [])),
            "deception_score": deception_score_val if isinstance(deception_score_val, (int, float)) else 0.0,
            "cross_platform_sources": len(results.get("cross_platform_intel", {})),
            "knowledge_base_entries": 1 if results.get("knowledge_integration", {}).get("knowledge_storage") else 0,
        }

        return stats

    except Exception as exc:
        _logger.debug("Summary statistics calculation error: %s", exc)
        return {"error": f"Statistics calculation failed: {exc}"}


def calculate_consolidation_metrics_from_crew(crew_result: Any, log: logging.Logger | None = None) -> dict[str, Any]:
    """Calculate knowledge consolidation metrics from CrewAI crew results.

    Args:
        crew_result: CrewAI crew output
        log: Optional logger for debugging

    Returns:
        Dictionary with consolidation metrics (score, depth, coverage, persistence)
    """
    try:
        if not crew_result:
            return {}

        crew_output = str(crew_result)

        # Calculate metrics based on crew output quality and depth
        consolidation_indicators = ["integrated", "consolidated", "archived", "stored", "processed"]
        consolidation_count = sum(1 for indicator in consolidation_indicators if indicator in crew_output.lower())

        metrics = {
            "consolidation_score": min(consolidation_count * 0.2, 1.0),
            "integration_depth": min(len(crew_output) / 1000, 1.0),
            "system_coverage": min(consolidation_count / 5, 1.0),
            "knowledge_persistence": True,
        }

        return metrics
    except Exception:
        return {}


def calculate_data_completeness(*data_sources, log: logging.Logger | None = None) -> float:
    """Calculate data completeness across all sources.

    Delegates to data_transformers module.

    Args:
        *data_sources: Variable number of data source dictionaries
        log: Optional logger for debugging

    Returns:
        Data completeness score (0.0-1.0)
    """
    try:
        # Lazy import to avoid circular dependencies
        from . import data_transformers

        return data_transformers.calculate_data_completeness(*data_sources)
    except Exception as exc:
        _logger = log or logger
        _logger.debug("Data completeness calculation error: %s", exc)
        return 0.0


def calculate_enhanced_summary_statistics(
    all_results: dict[str, Any], log: logging.Logger | None = None
) -> dict[str, Any]:
    """Calculate enhanced summary statistics from all analysis results.

    Delegates to data_transformers module.

    Args:
        all_results: Dictionary containing all analysis results
        log: Optional logger for debugging

    Returns:
        Dictionary with enhanced summary statistics
    """
    try:
        # Lazy import to avoid circular dependencies
        from . import data_transformers

        return data_transformers.calculate_enhanced_summary_statistics(all_results, log or logger)
    except Exception as exc:
        _logger = log or logger
        _logger.debug("Enhanced summary statistics calculation error: %s", exc)
        return {}


# Methods to be extracted:
# - calculate_ai_quality_score()
# - calculate_ai_enhancement_level()
# - calculate_confidence_interval()
# - calculate_synthesis_confidence()
# - calculate_synthesis_confidence_from_crew()
# - calculate_verification_confidence_from_crew()
# - calculate_overall_confidence()
# - calculate_transcript_quality()


# ============================================================================
# Category 3: Summary & Statistics
# ============================================================================

# Methods to be extracted:
# - calculate_summary_statistics()
# - calculate_enhanced_summary_statistics()
# - calculate_data_completeness()
# - calculate_consolidation_metrics_from_crew()


# ============================================================================
# Category 4: Resource Planning
# ============================================================================

# Methods to be extracted:
# - calculate_resource_requirements() (consolidate duplicates)
# - calculate_contextual_relevance_from_crew()
# - calculate_analysis_confidence_from_crew()


# ============================================================================
# Category 5: Insight Generation
# ============================================================================

# ═══════════════════════════════════════════════════════════════════════════════
# Category 5: Insight Generation
# ═══════════════════════════════════════════════════════════════════════════════


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
        return ["Apply standard intelligence protocols"]
