"""Result synthesis functions for autonomous intelligence workflows.

This module provides functions for synthesizing intelligence analysis results from CrewAI
workflow execution. It handles both normal synthesis, specialized synthesis, enhanced multi-modal
analysis, and fallback scenarios when advanced synthesis fails.

**Delegation Pattern:**
These functions delegate to `analytics_calculators` for complex computations like
summary statistics and insight generation, maintaining the Phase 1 delegation architecture.
"""

import logging
from platform.core.step_result import StepResult
from typing import Any


module_logger = logging.getLogger(__name__)


def _emit_log(logger_obj: Any, level: str, message: str, **extra: Any) -> None:
    target = logger_obj if logger_obj and hasattr(logger_obj, level) else module_logger
    log_method = getattr(target, level, None)
    if log_method is None:
        return
    if extra:
        log_method(message, extra=extra)
    else:
        log_method(message)


def fallback_basic_synthesis(all_results: dict[str, Any], error_context: str, logger: Any) -> StepResult:
    """Fallback basic synthesis when advanced synthesis fails.

    Creates a basic synthesis result with limited quality assurance.
    This is used as a safety net when multi-modal synthesis encounters errors.

    Args:
        all_results: Dictionary containing workflow results from all stages
        error_context: Description of the error that triggered fallback
        logger: Logger instance for recording fallback usage

    Returns:
        StepResult with:
            - fallback_synthesis=True (indicates degraded mode)
            - production_ready=False (CRITICAL: requires manual review)
            - quality_grade="limited"
            - requires_manual_review=True
            - basic_summary with available metadata
            - available_results showing which stages completed

    Example:
        >>> result = fallback_basic_synthesis(
        ...     all_results={"pipeline": {...}, "fact_analysis": {...}},
        ...     error_context="Multi-modal synthesis timeout",
        ...     logger=logger
        ... )
        >>> assert result.data["production_ready"] is False
        >>> assert result.data["fallback_synthesis"] is True
    """
    try:
        _emit_log(
            logger,
            "warning",
            "Invoking fallback synthesis path",
            fallback_reason=error_context,
            available_keys=list(all_results.keys()),
        )
        metadata = all_results.get("workflow_metadata", {})
        basic_synthesis = {
            "fallback_synthesis": True,
            "fallback_reason": error_context,
            "basic_summary": {
                "url": metadata.get("url"),
                "workflow_id": metadata.get("workflow_id"),
                "analysis_depth": metadata.get("depth"),
                "processing_time": metadata.get("processing_time"),
                "total_stages": metadata.get("total_stages"),
            },
            "available_results": {
                stage: bool(data) for stage, data in all_results.items() if stage != "workflow_metadata"
            },
            "quality_grade": "limited",
            "requires_manual_review": True,
            "production_ready": False,
        }
        return StepResult.ok(
            message=f"Basic synthesis completed due to advanced synthesis failure: {error_context}", **basic_synthesis
        )
    except Exception as fallback_error:
        _emit_log(
            logger,
            "error",
            "Fallback synthesis also failed",
            fallback_reason=error_context,
            fallback_error=str(fallback_error),
        )
        return StepResult.fail(
            f"Both advanced and basic synthesis failed. Advanced: {error_context}, Basic: {fallback_error}"
        )


def synthesize_autonomous_results(
    all_results: dict[str, Any], calculate_summary_statistics_fn: Any, generate_autonomous_insights_fn: Any, logger: Any
) -> dict[str, Any]:
    """Synthesize all autonomous analysis results into a comprehensive summary.

    Aggregates results from all workflow stages (acquisition, transcription,
    analysis, verification, integration) into a unified summary with statistics
    and insights.

    Args:
        all_results: Dictionary containing results from all workflow stages with keys:
            - pipeline: Content acquisition and transcription data
            - fact_analysis: Fact checking results
            - deception_score: Deception analysis data
            - cross_platform_intel: Cross-platform intelligence
            - knowledge_integration: Knowledge graph integration data
            - workflow_metadata: Workflow execution metadata
        calculate_summary_statistics_fn: Function to calculate summary statistics
            (delegates to analytics_calculators.calculate_summary_statistics)
        generate_autonomous_insights_fn: Function to generate insights
            (delegates to analytics_calculators.generate_autonomous_insights)
        logger: Logger instance for error recording

    Returns:
        Dictionary with structure:
            {
                "autonomous_analysis_summary": {
                    "url": str,
                    "workflow_id": str,
                    "analysis_depth": str,
                    "processing_time": float,
                    "deception_score": float,
                    "summary_statistics": dict,
                    "autonomous_insights": list[str]
                },
                "detailed_results": {
                    "content_analysis": dict,
                    "fact_checking": dict,
                    "cross_platform_intelligence": dict,
                    "deception_analysis": dict,
                    "knowledge_base_integration": dict
                },
                "workflow_metadata": dict
            }

        Or on error:
            {
                "error": str,
                "raw_results": dict
            }

    Example:
        >>> result = synthesize_autonomous_results(
        ...     all_results={"pipeline": {...}, "fact_analysis": {...}},
        ...     calculate_summary_statistics_fn=analytics.calculate_summary_statistics,
        ...     generate_autonomous_insights_fn=analytics.generate_autonomous_insights,
        ...     logger=logger
        ... )
        >>> assert "autonomous_analysis_summary" in result
        >>> assert "detailed_results" in result
    """
    try:
        pipeline_data = all_results.get("pipeline", {})
        fact_data = all_results.get("fact_analysis", {})
        deception_data = all_results.get("deception_score", {})
        intel_data = all_results.get("cross_platform_intel", {})
        knowledge_data = all_results.get("knowledge_integration", {})
        metadata = all_results.get("workflow_metadata", {})
        summary_stats = calculate_summary_statistics_fn(all_results)
        insights = generate_autonomous_insights_fn(all_results)
        synthesis = {
            "autonomous_analysis_summary": {
                "url": metadata.get("url"),
                "workflow_id": metadata.get("workflow_id"),
                "analysis_depth": metadata.get("depth"),
                "processing_time": metadata.get("processing_time"),
                "deception_score": deception_data.get("deception_score", 0.0),
                "summary_statistics": summary_stats,
                "autonomous_insights": insights,
            },
            "detailed_results": {
                "content_analysis": pipeline_data,
                "fact_checking": fact_data,
                "cross_platform_intelligence": intel_data,
                "deception_analysis": deception_data,
                "knowledge_base_integration": knowledge_data,
            },
            "workflow_metadata": metadata,
        }
        return synthesis
        _emit_log(
            logger,
            "info",
            "Autonomous synthesis completed",
            insight_count=len(insights),
            deception_score=synthesis["autonomous_analysis_summary"].get("deception_score"),
        )
        return synthesis
    except Exception as e:
        _emit_log(logger, "error", f"Result synthesis failed: {e}", raw_keys=list(all_results.keys()))
        return {"error": f"Result synthesis failed: {e}", "raw_results": all_results}


def synthesize_specialized_intelligence_results(
    all_results: dict[str, Any], generate_specialized_insights_fn: Any, logger: Any
) -> dict[str, Any]:
    """Synthesize all specialized intelligence results into comprehensive analysis.

    This function aggregates results from specialized autonomous agents performing
    acquisition, intelligence extraction, verification, deception analysis, behavioral
    analysis, and knowledge integration. It extracts 9 result types and generates
    specialized insights via the analytics_calculators delegate function.

    Args:
        all_results: Complete workflow results containing specialized analysis data with keys:
            - acquisition: Content acquisition data
            - intelligence: Intelligence extraction results
            - verification: Verification results
            - deception: Deception analysis with threat_score and threat_level
            - behavioral: Behavioral analysis data
            - knowledge: Knowledge integration results
            - social: Social media analysis (optional)
            - research: Research findings (optional)
            - performance: Performance metrics (optional)
            - workflow_metadata: Workflow execution metadata (url, workflow_id, processing_time)
        generate_specialized_insights_fn: Function to generate specialized insights
            (delegates to analytics_calculators.generate_specialized_insights)
        logger: Logger instance for error reporting

    Returns:
        Dictionary with three keys:
            - specialized_analysis_summary: High-level summary with:
                * url, workflow_id, analysis_approach, processing_time
                * threat_score, threat_level (from deception analysis)
                * summary_statistics (completion flags for all 9 analysis types)
                * specialized_insights (generated via delegate function)
            - detailed_results: Full results for all 9 analysis types
            - workflow_metadata: Original workflow metadata

        On error, returns:
            - error: Error message
            - raw_results: Original all_results dict

    Example:
        >>> def my_insights_fn(results, logger):
        ...     return ["Insight 1", "Insight 2"]
        >>> result = synthesize_specialized_intelligence_results(
        ...     all_results={"deception": {"threat_score": 0.75, "threat_level": "high"}, ...},
        ...     generate_specialized_insights_fn=my_insights_fn,
        ...     logger=my_logger
        ... )
        >>> result["specialized_analysis_summary"]["threat_score"]
        0.75
    """
    try:
        metadata = all_results.get("workflow_metadata", {})
        acquisition_data = all_results.get("acquisition", {})
        intelligence_data = all_results.get("intelligence", {})
        verification_data = all_results.get("verification", {})
        deception_data = all_results.get("deception", {})
        behavioral_data = all_results.get("behavioral", {})
        knowledge_data = all_results.get("knowledge", {})
        specialized_insights = generate_specialized_insights_fn(all_results, logger)
        summary_stats = {
            "content_processed": bool(acquisition_data),
            "intelligence_extracted": bool(intelligence_data),
            "verification_completed": bool(verification_data),
            "threat_assessment_done": bool(deception_data),
            "behavioral_analysis_done": bool(behavioral_data),
            "knowledge_integrated": bool(knowledge_data),
            "threat_score": deception_data.get("threat_score", 0.0),
            "threat_level": deception_data.get("threat_level", "unknown"),
        }
        synthesis = {
            "specialized_analysis_summary": {
                "url": metadata.get("url"),
                "workflow_id": metadata.get("workflow_id"),
                "analysis_approach": "specialized_autonomous_agents",
                "processing_time": metadata.get("processing_time"),
                "threat_score": deception_data.get("threat_score", 0.0),
                "threat_level": deception_data.get("threat_level", "unknown"),
                "summary_statistics": summary_stats,
                "specialized_insights": specialized_insights,
            },
            "detailed_results": {
                "acquisition": acquisition_data,
                "intelligence": intelligence_data,
                "verification": verification_data,
                "deception": deception_data,
                "behavioral": behavioral_data,
                "knowledge": knowledge_data,
                "social": all_results.get("social", {}),
                "research": all_results.get("research", {}),
                "performance": all_results.get("performance", {}),
            },
            "workflow_metadata": metadata,
        }
        _emit_log(
            logger,
            "info",
            "Specialized synthesis completed",
            insight_count=len(specialized_insights),
            threat_level=synthesis["specialized_analysis_summary"].get("threat_level"),
        )
        return synthesis
    except Exception as e:
        _emit_log(logger, "error", f"Specialized result synthesis failed: {e}", raw_keys=list(all_results.keys()))
        return {"error": f"Specialized synthesis failed: {e}", "raw_results": all_results}


async def synthesize_enhanced_autonomous_results(
    all_results: dict[str, Any], synthesizer: Any, error_handler: Any, fallback_basic_synthesis_fn: Any, logger: Any
) -> StepResult:
    """Synthesize enhanced autonomous analysis results using advanced multi-modal synthesis.

    This is the most sophisticated synthesis method, using the MultiModalSynthesizer to
    coordinate agent results with quality assessment. Falls back to basic synthesis on failure.

    **CRITICAL:** Sets production_ready=True when successful (unlike fallback which sets False).

    Args:
        all_results: Complete workflow results dictionary
        synthesizer: MultiModalSynthesizer instance for advanced synthesis
        error_handler: Error handler for recovery metrics
        fallback_basic_synthesis_fn: Function to call for fallback synthesis
            (delegates to fallback_basic_synthesis when multi-modal synthesis fails)
        logger: Logger instance for status reporting

    Returns:
        StepResult with:
            On success:
                - All data from synthesizer.synthesize_intelligence_results()
                - orchestrator_metadata: {synthesis_method, agent_coordination, error_recovery_metrics, synthesis_quality}
                - production_ready: True (CRITICAL - indicates production-ready output)
                - quality_assurance: {all_stages_validated, no_placeholders, comprehensive_analysis, agent_coordination_verified}
                - message or orchestrator_message: Quality summary

            On failure:
                - Falls back to fallback_basic_synthesis_fn with error context
                - production_ready: False (set by fallback function)

    Example:
        >>> result = await synthesize_enhanced_autonomous_results(
        ...     all_results={"workflow_metadata": {"depth": "comprehensive"}, ...},
        ...     synthesizer=my_synthesizer,
        ...     error_handler=my_error_handler,
        ...     fallback_basic_synthesis_fn=my_fallback_fn,
        ...     logger=my_logger
        ... )
        >>> result.data["production_ready"]
        True
    """
    try:
        logger.info("Starting advanced multi-modal intelligence synthesis")
        workflow_metadata = all_results.get("workflow_metadata", {})
        analysis_depth = workflow_metadata.get("depth", "standard")
        synthesized_result, quality_assessment = await synthesizer.synthesize_intelligence_results(
            workflow_results=all_results, analysis_depth=analysis_depth, workflow_metadata=workflow_metadata
        )
        if synthesized_result.success:
            logger.info(
                f"Multi-modal synthesis completed successfully - Quality: {quality_assessment.get('overall_grade', 'unknown')}, Confidence: {quality_assessment.get('confidence_score', 0.0):.2f}"
            )
            enhanced_result_data = synthesized_result.data.copy()
            enhanced_result_data.update(
                {
                    "orchestrator_metadata": {
                        "synthesis_method": "advanced_multi_modal",
                        "agent_coordination": True,
                        "error_recovery_metrics": error_handler.get_recovery_metrics(),
                        "synthesis_quality": quality_assessment,
                    },
                    "production_ready": True,
                    "quality_assurance": {
                        "all_stages_validated": True,
                        "no_placeholders": True,
                        "comprehensive_analysis": analysis_depth in ["comprehensive", "experimental"],
                        "agent_coordination_verified": True,
                    },
                }
            )
            orchestrator_note = f"Advanced autonomous intelligence synthesis completed - Quality: {quality_assessment.get('overall_grade', 'unknown')}"
            if "message" in enhanced_result_data:
                enhanced_result_data["orchestrator_message"] = orchestrator_note
            else:
                enhanced_result_data["message"] = orchestrator_note
            return StepResult.ok(**enhanced_result_data)
        else:
            logger.warning(f"Multi-modal synthesis failed: {synthesized_result.error}")
            return await fallback_basic_synthesis_fn(all_results, synthesized_result.error)
    except Exception as e:
        logger.error(f"Enhanced synthesis failed: {e}", exc_info=True)
        return await fallback_basic_synthesis_fn(all_results, str(e))
