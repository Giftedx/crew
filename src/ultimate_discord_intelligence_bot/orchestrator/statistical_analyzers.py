"""Statistical analysis and data consolidation utilities.

This module contains functions that calculate summary statistics, data completeness
metrics, and consolidation analysis from analysis results and CrewAI outputs.

Extracted from analytics_calculators.py to improve maintainability and organization.
"""

import logging
from typing import Any

logger = logging.getLogger(__name__)


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
        Completeness score between 0.0 and 1.0
    """
    try:
        # Import here to avoid circular dependencies
        from . import data_transformers

        return data_transformers.calculate_data_completeness(*data_sources, log=log)
    except Exception as exc:
        if log:
            log.debug("Data completeness calculation error: %s", exc)
        return 0.0


def calculate_enhanced_summary_statistics(
    results: dict[str, Any],
    include_quality_metrics: bool = True,
    include_temporal_analysis: bool = True,
    log: logging.Logger | None = None,
) -> dict[str, Any]:
    """Calculate enhanced summary statistics with optional quality and temporal analysis.

    Args:
        results: Dictionary containing all analysis results
        include_quality_metrics: Whether to include quality assessment metrics
        include_temporal_analysis: Whether to include temporal analysis metrics
        log: Optional logger for debugging

    Returns:
        Dictionary with enhanced summary statistics
    """
    _logger = log or logger
    try:
        # Get basic statistics
        basic_stats = calculate_summary_statistics(results, log=_logger)

        enhanced_stats = basic_stats.copy()

        # Add quality metrics if requested
        if include_quality_metrics:
            quality_data = results.get("quality_assessment", {})
            if isinstance(quality_data, dict):
                enhanced_stats.update(
                    {
                        "content_quality_score": quality_data.get("content_quality", 0.0),
                        "factual_accuracy_score": quality_data.get("factual_accuracy", 0.0),
                        "source_credibility_score": quality_data.get("source_credibility", 0.0),
                        "bias_detection_score": quality_data.get("bias_detection", 0.0),
                    }
                )

        # Add temporal analysis if requested
        if include_temporal_analysis:
            temporal_data = results.get("temporal_analysis", {})
            if isinstance(temporal_data, dict):
                enhanced_stats.update(
                    {
                        "temporal_coverage_days": temporal_data.get("coverage_days", 0),
                        "temporal_relevance_score": temporal_data.get("relevance_score", 0.0),
                        "historical_context_available": temporal_data.get("historical_context", False),
                    }
                )

        # Calculate overall completeness score
        data_sources = [results.get(key, {}) for key in ["pipeline", "fact_analysis", "quality_assessment"]]
        enhanced_stats["overall_completeness"] = calculate_data_completeness(*data_sources, log=_logger)

        return enhanced_stats

    except Exception as exc:
        _logger.debug("Enhanced summary statistics calculation error: %s", exc)
        return {"error": f"Enhanced statistics calculation failed: {exc}"}
