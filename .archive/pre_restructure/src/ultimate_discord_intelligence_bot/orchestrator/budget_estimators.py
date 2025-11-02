"""Budget estimation and resource calculation utilities.

This module contains functions for estimating costs, time requirements,
and resource needs for autonomous intelligence workflows.

Extracted from autonomous_orchestrator.py to improve maintainability.
"""

import logging
from typing import Any


logger = logging.getLogger(__name__)


def get_budget_limits(depth: str) -> dict[str, Any]:
    """Get budget limits based on analysis depth.

    Args:
        depth: Analysis depth level (standard, deep, comprehensive, experimental)

    Returns:
        Dictionary containing budget limits and thresholds
    """
    budget_config = {
        "standard": {
            "max_agents": 5,
            "max_tools": 10,
            "max_iterations": 3,
            "cost_limit_usd": 1.0,
            "time_limit_minutes": 15,
            "memory_limit_mb": 512,
        },
        "deep": {
            "max_agents": 8,
            "max_tools": 20,
            "max_iterations": 5,
            "cost_limit_usd": 3.0,
            "time_limit_minutes": 30,
            "memory_limit_mb": 1024,
        },
        "comprehensive": {
            "max_agents": 11,
            "max_tools": 30,
            "max_iterations": 7,
            "cost_limit_usd": 5.0,
            "time_limit_minutes": 45,
            "memory_limit_mb": 2048,
        },
        "experimental": {
            "max_agents": 15,
            "max_tools": 50,
            "max_iterations": 10,
            "cost_limit_usd": 10.0,
            "time_limit_minutes": 60,
            "memory_limit_mb": 4096,
        },
    }

    return budget_config.get(depth, budget_config["standard"])


def calculate_resource_requirements(depth: str) -> dict[str, Any]:
    """Calculate resource requirements for a given analysis depth.

    Args:
        depth: Analysis depth level

    Returns:
        Dictionary with CPU, memory, and storage requirements
    """
    base_requirements = {
        "standard": {
            "cpu_cores": 2,
            "memory_gb": 4,
            "storage_gb": 10,
            "gpu_required": False,
        },
        "deep": {
            "cpu_cores": 4,
            "memory_gb": 8,
            "storage_gb": 20,
            "gpu_required": False,
        },
        "comprehensive": {
            "cpu_cores": 6,
            "memory_gb": 16,
            "storage_gb": 30,
            "gpu_required": True,
        },
        "experimental": {
            "cpu_cores": 8,
            "memory_gb": 32,
            "storage_gb": 50,
            "gpu_required": True,
        },
    }

    return base_requirements.get(depth, base_requirements["standard"])


def estimate_workflow_duration(depth: str) -> dict[str, Any]:
    """Estimate workflow duration based on analysis depth.

    Args:
        depth: Analysis depth level

    Returns:
        Dictionary with duration estimates for each phase
    """
    duration_estimates = {
        "standard": {
            "acquisition": 60,  # seconds
            "transcription": 120,
            "analysis": 180,
            "verification": 60,
            "integration": 60,
            "total_seconds": 480,
            "total_minutes": 8,
        },
        "deep": {
            "acquisition": 90,
            "transcription": 180,
            "analysis": 300,
            "verification": 120,
            "integration": 90,
            "total_seconds": 780,
            "total_minutes": 13,
        },
        "comprehensive": {
            "acquisition": 120,
            "transcription": 240,
            "analysis": 480,
            "verification": 180,
            "integration": 120,
            "total_seconds": 1140,
            "total_minutes": 19,
        },
        "experimental": {
            "acquisition": 180,
            "transcription": 300,
            "analysis": 720,
            "verification": 300,
            "integration": 180,
            "total_seconds": 1680,
            "total_minutes": 28,
        },
    }

    return duration_estimates.get(depth, duration_estimates["standard"])


def calculate_cost_estimate(depth: str, model_pricing: dict[str, float] | None = None) -> dict[str, Any]:
    """Calculate estimated cost for workflow execution.

    Args:
        depth: Analysis depth level
        model_pricing: Optional custom model pricing (per 1K tokens)

    Returns:
        Dictionary with cost breakdown by component
    """
    if model_pricing is None:
        # Default pricing per 1K tokens
        model_pricing = {
            "gpt-4": 0.03,
            "gpt-3.5-turbo": 0.001,
            "claude-2": 0.008,
            "llama-2": 0.0005,
        }

    # Estimated token usage by depth
    token_usage = {
        "standard": {
            "transcription": 5000,
            "analysis": 10000,
            "verification": 3000,
            "integration": 2000,
            "total": 20000,
        },
        "deep": {
            "transcription": 10000,
            "analysis": 25000,
            "verification": 8000,
            "integration": 5000,
            "total": 48000,
        },
        "comprehensive": {
            "transcription": 20000,
            "analysis": 50000,
            "verification": 15000,
            "integration": 10000,
            "total": 95000,
        },
        "experimental": {
            "transcription": 40000,
            "analysis": 100000,
            "verification": 30000,
            "integration": 20000,
            "total": 190000,
        },
    }

    tokens = token_usage.get(depth, token_usage["standard"])
    model = "gpt-3.5-turbo" if depth == "standard" else "gpt-4"
    price_per_1k = model_pricing.get(model, 0.001)

    return {
        "model": model,
        "tokens": tokens,
        "price_per_1k": price_per_1k,
        "estimated_cost": (tokens["total"] / 1000) * price_per_1k,
        "breakdown": {phase: (count / 1000) * price_per_1k for phase, count in tokens.items() if phase != "total"},
    }


def get_ai_enhancement_level(depth: str) -> float:
    """Calculate AI enhancement level based on depth.

    Args:
        depth: Analysis depth level

    Returns:
        AI enhancement level as a float between 0.0 and 1.0
    """
    enhancement_levels = {
        "standard": 0.25,
        "deep": 0.50,
        "comprehensive": 0.75,
        "experimental": 1.00,
    }

    return enhancement_levels.get(depth, 0.25)
