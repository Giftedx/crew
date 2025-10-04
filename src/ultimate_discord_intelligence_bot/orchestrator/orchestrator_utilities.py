"""Orchestrator Utility Functions - Budget Management and System Utilities.

This module provides utility functions for the autonomous orchestrator:
- Budget calculations based on analysis depth
- Tenant context preservation for async operations
- Agent workflow mapping initialization

Extracted from autonomous_orchestrator.py (Week 4 Session 3) to achieve <5,000 line target.

Functions:
    get_budget_limits(depth: str) -> dict[str, Any]:
        Calculate budget limits for different analysis depths

    to_thread_with_tenant(fn, *args, **kwargs):
        Execute sync function in thread while preserving tenant context

    initialize_agent_workflow_map() -> dict[str, str]:
        Create mapping of workflow names to agent method names

    initialize_workflow_dependencies() -> dict[str, list[str]]:
        Define workflow execution dependencies
"""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:  # pragma: no cover - typing only
    pass


def get_budget_limits(depth: str) -> dict[str, Any]:
    """Get budget limits based on analysis depth.

    Budget tiers reflect the complexity and cost of each depth level.
    Higher depths use more expensive models and produce longer outputs.

    Args:
        depth: Analysis depth (quick/standard/deep/comprehensive/experimental)

    Returns:
        Dictionary with 'total' budget and 'per_task' limits

    Examples:
        >>> limits = get_budget_limits("standard")
        >>> limits["total"]
        1.5
        >>> limits["per_task"]["analysis"]
        0.75

        >>> limits = get_budget_limits("experimental")
        >>> limits["total"]
        10.0
    """
    budgets = {
        "quick": {
            "total": 0.50,  # $0.50 total
            "per_task": {
                "acquisition": 0.05,
                "transcription": 0.15,
                "analysis": 0.30,
            },
        },
        "standard": {
            "total": 1.50,  # $1.50 total
            "per_task": {
                "acquisition": 0.05,
                "transcription": 0.30,
                "analysis": 0.75,
                "verification": 0.40,
            },
        },
        "deep": {
            "total": 3.00,  # $3.00 total
            "per_task": {
                "acquisition": 0.05,
                "transcription": 0.50,
                "analysis": 1.20,
                "verification": 0.75,
                "knowledge": 0.50,
            },
        },
        "comprehensive": {
            "total": 5.00,  # $5.00 total
            "per_task": {
                "acquisition": 0.10,
                "transcription": 0.75,
                "analysis": 2.00,
                "verification": 1.00,
                "knowledge": 1.15,
            },
        },
        "experimental": {
            "total": 10.00,  # $10.00 total
            "per_task": {
                "acquisition": 0.10,
                "transcription": 1.50,
                "analysis": 4.00,
                "verification": 2.00,
                "knowledge": 2.40,
            },
        },
    }

    return budgets.get(depth, budgets["standard"])


async def to_thread_with_tenant(fn, *args, **kwargs):
    """Run a sync function in a thread while preserving TenantContext.

    Many tools rely on tenant-scoped services. Ensure we propagate the
    current TenantContext into worker threads so data reads/writes hit the
    right namespaces.

    Args:
        fn: Synchronous function to execute
        *args: Positional arguments for fn
        **kwargs: Keyword arguments for fn

    Returns:
        Result of fn(*args, **kwargs)

    Examples:
        >>> async def example():
        ...     result = await to_thread_with_tenant(some_sync_function, arg1, arg2)
        ...     return result
    """
    try:
        # Import here to avoid circular dependencies
        from ..tenancy import current_tenant, with_tenant

        ctx = current_tenant()

        def _call():
            if ctx is not None:
                with with_tenant(ctx):
                    return fn(*args, **kwargs)
            return fn(*args, **kwargs)

        return await asyncio.to_thread(_call)
    except Exception:
        # Fallback if tenancy not available or import fails
        return await asyncio.to_thread(fn, *args, **kwargs)


def initialize_agent_workflow_map() -> dict[str, str]:
    """Initialize mapping of workflow names to agent method names.

    CRITICAL: This returns agent method NAMES (strings), not instances.
    Agents will be lazy-loaded via _get_or_create_agent() when needed.

    Returns:
        Dictionary mapping workflow names to agent method names

    Examples:
        >>> workflow_map = initialize_agent_workflow_map()
        >>> workflow_map["content_acquisition"]
        'multi_platform_acquisition_specialist'
        >>> workflow_map["content_analysis"]
        'comprehensive_linguistic_analyst'
    """
    return {
        "mission_coordination": "autonomous_mission_coordinator",
        "content_acquisition": "multi_platform_acquisition_specialist",
        "transcription_processing": "advanced_transcription_engineer",
        "content_analysis": "comprehensive_linguistic_analyst",
        "information_verification": "information_verification_director",
        "threat_analysis": "threat_intelligence_analyst",
        "behavioral_profiling": "behavioral_profiling_specialist",
        "social_intelligence": "social_intelligence_coordinator",
        "trend_analysis": "trend_analysis_scout",
        "knowledge_integration": "knowledge_integration_architect",
        "research_synthesis": "research_synthesis_specialist",
        "intelligence_briefing": "intelligence_briefing_director",
        "strategic_argumentation": "strategic_argument_analyst",
        "system_operations": "system_operations_manager",
        "community_engagement": "community_engagement_coordinator",
    }


def initialize_workflow_dependencies() -> dict[str, list[str]]:
    """Define workflow execution dependencies.

    Returns a dependency graph showing which workflows must complete
    before others can begin. Used for parallel execution planning.

    Returns:
        Dictionary mapping workflow names to lists of prerequisite workflows

    Examples:
        >>> dependencies = initialize_workflow_dependencies()
        >>> dependencies["content_acquisition"]
        ['mission_coordination']
        >>> dependencies["knowledge_integration"]
        ['information_verification', 'threat_analysis', 'behavioral_profiling']
    """
    return {
        "mission_coordination": [],  # Entry point - coordinates all other workflows
        "content_acquisition": ["mission_coordination"],
        "transcription_processing": ["content_acquisition"],
        "content_analysis": ["transcription_processing"],
        "information_verification": ["content_analysis"],
        "threat_analysis": ["content_analysis", "information_verification"],
        "behavioral_profiling": ["content_analysis", "threat_analysis"],
        "social_intelligence": ["content_analysis"],  # Can run in parallel
        "trend_analysis": ["social_intelligence"],  # Depends on social intelligence
        "knowledge_integration": ["information_verification", "threat_analysis", "behavioral_profiling"],
        "research_synthesis": ["content_analysis", "information_verification"],
        "intelligence_briefing": ["knowledge_integration", "research_synthesis"],
        "strategic_argumentation": ["information_verification", "research_synthesis"],
        "system_operations": [],  # Monitoring workflow - runs independently
        "community_engagement": ["intelligence_briefing"],  # Final stage
    }
