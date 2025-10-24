"""Workflow planning and capability management for autonomous intelligence orchestration.

This module provides workflow planning utilities including duration estimation,
stage planning, and capability enumeration. All functions are stateless and take
configuration parameters (like depth) to return planning information.

Extracted from autonomous_orchestrator.py as part of Week 4 decomposition initiative.
"""

from __future__ import annotations

from typing import Any


def get_available_capabilities() -> list[str]:
    """Get list of all available autonomous capabilities.

    Returns:
        List of capability identifiers representing all available autonomous
        intelligence capabilities in the system.

    Example:
        >>> caps = get_available_capabilities()
        >>> len(caps)
        15
        >>> "multi_platform_content_acquisition" in caps
        True
    """
    return [
        "multi_platform_content_acquisition",
        "advanced_transcription_indexing",
        "comprehensive_linguistic_analysis",
        "multi_source_fact_verification",
        "advanced_threat_deception_analysis",
        "cross_platform_social_intelligence",
        "behavioral_profiling_persona_analysis",
        "multi_layer_knowledge_integration",
        "research_synthesis_context_building",
        "predictive_performance_analytics",
        "ai_enhanced_quality_assessment",
        "intelligence_briefing_curation",
        "autonomous_learning_adaptation",
        "real_time_monitoring_alerts",
        "community_liaison_communication",
    ]


def estimate_workflow_duration(depth: str) -> dict[str, Any]:
    """Estimate workflow duration based on depth and complexity.

    Args:
        depth: Analysis depth level (standard, deep, comprehensive, experimental)

    Returns:
        Dictionary containing:
        - estimated_minutes: Expected duration in minutes
        - confidence_interval: Uncertainty range (±20%)
        - factors: List of factors affecting duration

    Example:
        >>> duration = estimate_workflow_duration("standard")
        >>> duration["estimated_minutes"]
        3
        >>> duration = estimate_workflow_duration("experimental")
        >>> duration["estimated_minutes"]
        25
    """
    base_duration_minutes = {
        "standard": 3,
        "deep": 8,
        "comprehensive": 15,
        "experimental": 25,
    }

    return {
        "estimated_minutes": base_duration_minutes.get(depth, 5),
        "confidence_interval": "±20%",
        "factors": ["content_complexity", "network_latency", "ai_model_response_times"],
    }


def get_planned_stages(depth: str) -> list[dict[str, Any]]:
    """Get planned workflow stages based on analysis depth.

    Different depth levels include different stages based on priority:
    - standard: critical + high priority stages
    - deep: critical + high + medium priority stages
    - comprehensive/experimental: all stages

    Args:
        depth: Analysis depth level (standard, deep, comprehensive, experimental)

    Returns:
        List of stage dictionaries, each containing:
        - name: Stage name
        - agent: Responsible agent identifier
        - priority: Stage priority (critical/high/medium/low)

    Example:
        >>> stages = get_planned_stages("standard")
        >>> len(stages)  # Only critical + high priority
        7
        >>> stages = get_planned_stages("comprehensive")
        >>> len(stages)  # All stages
        14
    """
    all_stages = [
        {
            "name": "Mission Planning",
            "agent": "mission_orchestrator",
            "priority": "critical",
        },
        {
            "name": "Content Acquisition",
            "agent": "acquisition_specialist",
            "priority": "critical",
        },
        {
            "name": "Transcription Analysis",
            "agent": "transcription_engineer",
            "priority": "high",
        },
        {
            "name": "Content Analysis",
            "agent": "analysis_cartographer",
            "priority": "critical",
        },
        {
            "name": "Information Verification",
            "agent": "verification_director",
            "priority": "high",
        },
        {
            "name": "Threat Analysis",
            "agent": "risk_intelligence_analyst",
            "priority": "high",
        },
        {
            "name": "Social Intelligence",
            "agent": "signal_recon_specialist",
            "priority": "medium",
        },
        {
            "name": "Behavioral Profiling",
            "agent": "persona_archivist",
            "priority": "medium",
        },
        {
            "name": "Knowledge Integration",
            "agent": "knowledge_integrator",
            "priority": "high",
        },
        {
            "name": "Research Synthesis",
            "agent": "research_synthesist",
            "priority": "medium",
        },
        {
            "name": "Performance Analytics",
            "agent": "system_reliability_officer",
            "priority": "low",
        },
        {
            "name": "Quality Assessment",
            "agent": "intelligence_briefing_curator",
            "priority": "low",
        },
        {
            "name": "Intelligence Briefing",
            "agent": "intelligence_briefing_curator",
            "priority": "high",
        },
        {
            "name": "Communication Reporting",
            "agent": "community_liaison",
            "priority": "medium",
        },
    ]

    stage_filters = {
        "standard": lambda s: s["priority"] in ["critical", "high"],
        "deep": lambda s: s["priority"] in ["critical", "high", "medium"],
        "comprehensive": lambda s: True,
        "experimental": lambda s: True,
    }

    filter_func = stage_filters.get(depth, stage_filters["standard"])
    return [stage for stage in all_stages if filter_func(stage)]


def get_capabilities_summary(depth: str) -> dict[str, Any]:
    """Get summary of capabilities used in this workflow.

    Provides an overview of the workflow configuration including agent count,
    tool count, and AI enhancement features.

    Args:
        depth: Analysis depth level (standard, deep, comprehensive, experimental)

    Returns:
        Dictionary containing:
        - total_agents: Number of agents planned for this depth
        - total_tools: Total number of available capabilities
        - ai_enhancement_features: List of AI enhancement feature identifiers
        - depth_level: The depth level used
        - experimental_features_enabled: Whether experimental features are active

    Example:
        >>> summary = get_capabilities_summary("experimental")
        >>> summary["experimental_features_enabled"]
        True
        >>> summary["total_tools"]
        15
    """
    return {
        "total_agents": len(get_planned_stages(depth)),
        "total_tools": len(get_available_capabilities()),
        "ai_enhancement_features": [
            "adaptive_workflow_planning",
            "real_time_performance_monitoring",
            "multi_agent_coordination",
            "predictive_analytics",
            "autonomous_learning",
        ],
        "depth_level": depth,
        "experimental_features_enabled": depth == "experimental",
    }
