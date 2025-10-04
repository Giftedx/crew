"""Result synthesis functions for autonomous intelligence workflows.

This module provides functions for synthesizing intelligence analysis results
from CrewAI workflow execution. Extracted from autonomous_orchestrator.py as
part of Phase 2 Week 5 refactoring.

Functions handle:
- Basic fallback synthesis when advanced synthesis fails
- Autonomous results synthesis with summary statistics
- Enhanced multi-modal synthesis coordination
- Specialized intelligence results synthesis

All functions maintain the delegation pattern established in Phase 1,
calling analytics_calculators for insights and statistics generation.
"""

from typing import Any

from ultimate_discord_intelligence_bot.step_result import StepResult


def fallback_basic_synthesis(
    all_results: dict[str, Any],
    error_context: str,
    logger: Any,
) -> StepResult:
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
        # Extract basic components
        metadata = all_results.get("workflow_metadata", {})

        # Create basic synthesis result
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
            message=f"Basic synthesis completed due to advanced synthesis failure: {error_context}",
            **basic_synthesis,
        )

    except Exception as fallback_error:
        return StepResult.fail(
            f"Both advanced and basic synthesis failed. Advanced: {error_context}, Basic: {fallback_error}"
        )


def synthesize_autonomous_results(
    all_results: dict[str, Any],
    calculate_summary_statistics_fn: Any,
    generate_autonomous_insights_fn: Any,
    logger: Any,
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
        # Extract key metrics and insights
        pipeline_data = all_results.get("pipeline", {})
        fact_data = all_results.get("fact_analysis", {})
        deception_data = all_results.get("deception_score", {})
        intel_data = all_results.get("cross_platform_intel", {})
        knowledge_data = all_results.get("knowledge_integration", {})
        metadata = all_results.get("workflow_metadata", {})

        # Calculate summary statistics (delegates to analytics_calculators)
        summary_stats = calculate_summary_statistics_fn(all_results)

        # Generate autonomous insights (delegates to analytics_calculators)
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

    except Exception as e:
        logger.error(f"Result synthesis failed: {e}", exc_info=True)
        return {"error": f"Result synthesis failed: {e}", "raw_results": all_results}
