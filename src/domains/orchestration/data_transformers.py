"""Data transformation functions for pipeline results and intelligence reports.

This module provides functions for normalizing, merging, transforming, and aggregating
data across different pipeline stages and analysis outputs.
"""

import logging
from platform.core.step_result import StepResult
from typing import Any


# Module-level logger
logger = logging.getLogger(__name__)


def normalize_acquisition_data(
    acquisition: StepResult | dict[str, Any] | None,
) -> dict[str, Any]:
    """Return a flattened ContentPipeline payload for downstream stages.

    The ContentPipeline tool historically wrapped results inside nested ``data``
    structures. This helper unifies both legacy and new shapes so all stages
    can reliably access ``download`` / ``transcription`` / ``analysis`` blocks
    without duplicating guard logic.

    Args:
        acquisition: Acquisition result as StepResult or dict

    Returns:
        Flattened dictionary with pipeline data
    """
    if isinstance(acquisition, StepResult):
        data = acquisition.data
    elif isinstance(acquisition, dict):
        data = acquisition
    else:
        return {}

    if not isinstance(data, dict):
        return {}

    if any(key in data for key in ("transcription", "analysis", "download", "fallacy", "perspective")):
        return data

    nested = data.get("data")
    if isinstance(nested, dict):
        return nested

    raw_payload = data.get("raw_pipeline_payload")
    if isinstance(raw_payload, dict):
        return raw_payload

    return data


def merge_threat_and_deception_data(threat_result: StepResult, deception_result: StepResult) -> StepResult:
    """Combine threat analysis output with deception scoring metrics (StepResult inputs).

    Note: Retained for backward compatibility where StepResult objects are used.

    Args:
        threat_result: Threat analysis results
        deception_result: Deception scoring results

    Returns:
        Combined StepResult with threat and deception data
    """
    if not isinstance(threat_result, StepResult):
        return threat_result
    if not threat_result.success:
        return threat_result

    combined_data: dict[str, Any] = dict(threat_result.data)
    original_message = combined_data.get("message")

    if isinstance(deception_result, StepResult) and deception_result.success:
        deception_payload = dict(deception_result.data)
        if deception_payload:
            combined_data["deception_metrics"] = deception_payload
            if "deception_score" not in combined_data and "deception_score" in deception_payload:
                combined_data["deception_score"] = deception_payload.get("deception_score")
    else:
        status = None
        error_message = None
        if isinstance(deception_result, StepResult):
            status = deception_result.custom_status
            error_message = deception_result.error
        combined_data["deception_metrics"] = {
            "status": status or "skipped",
            "error": error_message,
            "deception_score": None,
        }

    return StepResult.ok(
        data=combined_data,
        message=original_message or "Combined threat + deception analysis",
    )


def transform_evidence_to_verdicts(
    fact_verification_data: dict[str, Any],
    logger_instance: logging.Logger | None = None,
) -> list[dict[str, Any]]:
    """Transform fact-check evidence into verdict format for deception scoring.

    Args:
        fact_verification_data: Fact verification results
        logger_instance: Optional logger instance

    Returns:
        List of verdict dictionaries
    """
    _logger = logger_instance or logger

    # Prefer explicit per-claim items if present
    items = fact_verification_data.get("items")
    out: list[dict[str, Any]] = []
    if isinstance(items, list) and items:
        for it in items:
            if isinstance(it, dict):
                verdict = it.get("verdict")
                if isinstance(verdict, str) and verdict.strip():
                    try:
                        conf_raw = it.get("confidence", 0.5)
                        conf = float(conf_raw) if isinstance(conf_raw, (int, float, str)) else 0.5
                    except Exception:
                        conf = 0.5
                    out.append(
                        {
                            "verdict": verdict.strip().lower(),
                            "confidence": max(0.0, min(conf, 1.0)),
                            "claim": it.get("claim"),
                            "source": it.get("source", "factcheck"),
                            "source_trust": it.get("source_trust"),
                            "salience": 1.0,
                        }
                    )
        if out:
            return out

    # Fallback: synthesize verdicts from evidence quantity
    evidence = fact_verification_data.get("evidence", [])
    factchecks: list[dict[str, Any]] = []
    claim = fact_verification_data.get("claim", "Unknown claim")
    evidence_count = len(evidence) if isinstance(evidence, list) else 0
    if evidence_count <= 0:
        factchecks.append(
            {
                "verdict": "uncertain",
                "confidence": 0.3,
                "claim": claim,
                "source": "evidence_search",
                "salience": 1.0,
            }
        )
    elif evidence_count >= 3:
        factchecks.append(
            {
                "verdict": "needs context",
                "confidence": 0.6,
                "claim": claim,
                "source": "multi_source_evidence",
                "salience": 1.0,
            }
        )
    else:
        factchecks.append(
            {
                "verdict": "uncertain",
                "confidence": 0.4,
                "claim": claim,
                "source": "limited_evidence",
                "salience": 1.0,
            }
        )
    return factchecks


def extract_fallacy_data(logical_analysis_data: dict[str, Any]) -> list[dict[str, Any]]:
    """Extract fallacy data from logical analysis results.

    Args:
        logical_analysis_data: Logical analysis results

    Returns:
        List of fallacy dictionaries
    """
    fallacies = []

    # Look for fallacies in various possible formats
    if isinstance(logical_analysis_data.get("fallacies"), list):
        for fallacy in logical_analysis_data["fallacies"]:
            if isinstance(fallacy, dict):
                fallacies.append(fallacy)
            elif isinstance(fallacy, str):
                fallacies.append({"type": fallacy, "confidence": 0.7})
    elif isinstance(logical_analysis_data.get("fallacies_detected"), list):
        for fallacy in logical_analysis_data["fallacies_detected"]:
            if isinstance(fallacy, dict):
                fallacies.append(fallacy)
            elif isinstance(fallacy, str):
                fallacies.append({"type": fallacy, "confidence": 0.7})

    return fallacies


def calculate_data_completeness(*data_sources) -> float:
    """Calculate data completeness across all sources.

    Args:
        *data_sources: Variable number of data dictionaries

    Returns:
        Completeness ratio between 0.0 and 1.0
    """
    try:
        non_empty_sources = sum(1 for source in data_sources if source and isinstance(source, dict) and len(source) > 0)
        total_sources = len(data_sources)
        return non_empty_sources / total_sources if total_sources > 0 else 0.0
    except Exception:
        return 0.0


def assign_intelligence_grade(
    analysis_data: dict[str, Any],
    threat_data: dict[str, Any],
    verification_data: dict[str, Any],
) -> str:
    """Assign intelligence grade based on analysis quality.

    Args:
        analysis_data: Analysis results
        threat_data: Threat analysis results
        verification_data: Verification results

    Returns:
        Grade string: "A" (high), "B" (good), "C" (acceptable), "D" (limited)
    """
    try:
        threat_level = threat_data.get("threat_level", "unknown")
        has_verification = bool(verification_data.get("fact_checks"))
        has_analysis = bool(analysis_data.get("transcript"))

        if threat_level != "unknown" and has_verification and has_analysis:
            return "A"  # High quality
        elif (threat_level != "unknown" and has_verification) or (has_verification and has_analysis):
            return "B"  # Good quality
        elif has_analysis:
            return "C"  # Acceptable quality
        else:
            return "D"  # Limited quality
    except Exception:
        return "C"


def calculate_enhanced_summary_statistics(
    all_results: dict[str, Any],
    logger_instance: logging.Logger | None = None,
) -> dict[str, Any]:
    """Calculate enhanced summary statistics from all analysis results.

    Args:
        all_results: All analysis results
        logger_instance: Optional logger instance

    Returns:
        Dictionary of summary statistics
    """
    _logger = logger_instance or logger
    try:
        stats = {}

        # Count successful analysis stages
        successful_stages = sum(1 for result in all_results.values() if isinstance(result, dict) and len(result) > 0)
        stats["successful_stages"] = successful_stages
        stats["total_stages_attempted"] = len(all_results)

        # Calculate processing metrics
        metadata = all_results.get("workflow_metadata", {})
        stats["processing_time"] = metadata.get("processing_time", 0.0)
        stats["capabilities_used"] = len(metadata.get("capabilities_used", []))

        # Extract content metrics
        transcription_data = all_results.get("transcription", {})
        if transcription_data:
            stats["transcript_length"] = len(transcription_data.get("transcript", ""))

        # Calculate analysis depth metrics
        verification_data = all_results.get("information_verification", {})
        if verification_data:
            stats["fact_checks_performed"] = len(verification_data.get("fact_checks", {}))

        threat_data = all_results.get("threat_analysis", {})
        if threat_data:
            stats["threat_indicators_found"] = len(threat_data.get("deception_analysis", {}))

        return stats
    except Exception as e:
        _logger.error(f"Statistics calculation failed: {e}")
        return {"error": f"Statistics calculation failed: {e}"}


def generate_comprehensive_intelligence_insights(
    all_results: dict[str, Any],
    logger_instance: logging.Logger | None = None,
) -> list[str]:
    """Generate comprehensive intelligence insights from all analysis results.

    Args:
        all_results: All analysis results
        logger_instance: Optional logger instance

    Returns:
        List of insight strings
    """
    _logger = logger_instance or logger
    try:
        insights = []

        # Add threat assessment insights
        threat_data = all_results.get("threat_analysis", {})
        if threat_data:
            threat_level = threat_data.get("threat_level", "unknown")
            insights.append(f"🛡️ Threat Assessment: {threat_level.upper()} level detected")

        # Add verification insights
        verification_data = all_results.get("information_verification", {})
        if verification_data:
            fact_checks = verification_data.get("fact_checks", {})
            if fact_checks:
                insights.append(f"✅ Information Verification: {len(fact_checks)} claims analyzed")

        # Add behavioral insights
        behavioral_data = all_results.get("behavioral_profiling", {})
        if behavioral_data:
            risk_score = behavioral_data.get("behavioral_risk_score", 0.0)
            insights.append(f"👤 Behavioral Risk Score: {risk_score:.2f}")

        # Add research insights
        research_data = all_results.get("research_synthesis", {})
        if research_data:
            research_topics = research_data.get("research_topics", [])
            if research_topics:
                insights.append(f"📚 Research Topics Analyzed: {len(research_topics)}")

        # Add content quality insights
        content_data = all_results.get("content_analysis", {})
        if content_data:
            quality_score = content_data.get("quality_score", 0.0)
            if quality_score > 0:
                insights.append(f"📊 Content Quality Score: {quality_score:.2f}")

        return insights
    except Exception as e:
        _logger.error(f"Insights generation failed: {e}")
        return [f"⚠️ Insights generation failed: {e}"]
