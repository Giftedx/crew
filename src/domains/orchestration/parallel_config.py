"""Configuration and settings for parallel execution optimization.

This module provides configuration management for parallel task execution,
including automatic detection of optimal parallelization settings based on
system capabilities and workload characteristics.
"""

import logging
import os
from typing import Any


logger = logging.getLogger(__name__)


def get_parallel_execution_config() -> dict[str, Any]:
    """Get optimized parallel execution configuration.

    This function determines the best parallel execution settings based on:
    - System capabilities (CPU cores, memory)
    - Environment variables
    - Workload characteristics

    Returns:
        Dictionary with parallel execution configuration
    """
    # Get system capabilities
    cpu_count = os.cpu_count() or 4
    memory_gb = _get_available_memory_gb()

    # Default configuration
    config = {
        "enable_parallel_analysis": True,
        "enable_parallel_fact_checking": True,
        "enable_parallel_memory_ops": True,
        "max_concurrent_tasks": min(cpu_count, 6),  # Cap at 6 for stability
        "parallel_execution_threshold": 3,  # Minimum tasks for parallel execution
        "memory_efficient_mode": memory_gb < 8,  # Enable if low memory
        "cpu_efficient_mode": cpu_count < 4,  # Enable if low CPU
    }

    # Override with environment variables if set
    config.update(_get_env_overrides())

    # Apply intelligent optimizations
    config = _apply_intelligent_optimizations(config, cpu_count, memory_gb)

    logger.info(f"⚡ Parallel execution config: {config}")
    return config


def _get_available_memory_gb() -> float:
    """Get available system memory in GB."""
    try:
        import psutil

        return psutil.virtual_memory().total / (1024**3)
    except ImportError:
        # Fallback: assume 8GB if psutil not available
        return 8.0


def _get_env_overrides() -> dict[str, Any]:
    """Get configuration overrides from environment variables."""
    overrides = {}

    # Parallel execution flags
    if "ENABLE_PARALLEL_ANALYSIS" in os.environ:
        overrides["enable_parallel_analysis"] = os.environ["ENABLE_PARALLEL_ANALYSIS"].lower() == "true"

    if "ENABLE_PARALLEL_FACT_CHECKING" in os.environ:
        overrides["enable_parallel_fact_checking"] = os.environ["ENABLE_PARALLEL_FACT_CHECKING"].lower() == "true"

    if "ENABLE_PARALLEL_MEMORY_OPS" in os.environ:
        overrides["enable_parallel_memory_ops"] = os.environ["ENABLE_PARALLEL_MEMORY_OPS"].lower() == "true"

    # Performance tuning
    if "MAX_CONCURRENT_TASKS" in os.environ:
        try:
            overrides["max_concurrent_tasks"] = int(os.environ["MAX_CONCURRENT_TASKS"])
        except ValueError:
            logger.warning(f"Invalid MAX_CONCURRENT_TASKS value: {os.environ['MAX_CONCURRENT_TASKS']}")

    if "PARALLEL_EXECUTION_THRESHOLD" in os.environ:
        try:
            overrides["parallel_execution_threshold"] = int(os.environ["PARALLEL_EXECUTION_THRESHOLD"])
        except ValueError:
            logger.warning(f"Invalid PARALLEL_EXECUTION_THRESHOLD value: {os.environ['PARALLEL_EXECUTION_THRESHOLD']}")

    return overrides


def _apply_intelligent_optimizations(config: dict[str, Any], cpu_count: int, memory_gb: float) -> dict[str, Any]:
    """Apply intelligent optimizations based on system capabilities."""

    # Memory-based optimizations
    if memory_gb < 4:
        logger.warning("⚠️  Low memory detected, disabling parallel memory operations")
        config["enable_parallel_memory_ops"] = False
        config["max_concurrent_tasks"] = min(config["max_concurrent_tasks"], 2)
    elif memory_gb < 8:
        config["max_concurrent_tasks"] = min(config["max_concurrent_tasks"], 4)

    # CPU-based optimizations
    if cpu_count < 2:
        logger.warning("⚠️  Low CPU count detected, disabling parallel execution")
        config["enable_parallel_analysis"] = False
        config["enable_parallel_fact_checking"] = False
        config["max_concurrent_tasks"] = 1
    elif cpu_count < 4:
        config["max_concurrent_tasks"] = min(config["max_concurrent_tasks"], 3)

    # Workload-based optimizations
    if config["memory_efficient_mode"]:
        logger.info("🔧 Enabling memory-efficient parallel execution")
        config["enable_parallel_memory_ops"] = False

    if config["cpu_efficient_mode"]:
        logger.info("🔧 Enabling CPU-efficient parallel execution")
        config["max_concurrent_tasks"] = min(config["max_concurrent_tasks"], 2)

    return config


def get_optimal_crew_process_type(task_count: int, config: dict[str, Any]) -> str:
    """Determine optimal CrewAI process type based on task count and configuration.

    Args:
        task_count: Number of tasks in the crew
        config: Parallel execution configuration

    Returns:
        Optimal process type ("sequential", "hierarchical")
    """
    if task_count < config["parallel_execution_threshold"]:
        return "sequential"

    if (
        config["enable_parallel_analysis"]
        or config["enable_parallel_fact_checking"]
        or config["enable_parallel_memory_ops"]
    ):
        return "hierarchical"

    return "sequential"


def estimate_performance_improvement(task_count: int, config: dict[str, Any]) -> dict[str, Any]:
    """Estimate performance improvement from parallel execution.

    Args:
        task_count: Number of tasks in the crew
        config: Parallel execution configuration

    Returns:
        Dictionary with performance estimates
    """
    if not any(
        [
            config["enable_parallel_analysis"],
            config["enable_parallel_fact_checking"],
            config["enable_parallel_memory_ops"],
        ]
    ):
        return {
            "parallelization_feasible": False,
            "estimated_time_savings_percent": 0.0,
            "estimated_speedup_factor": 1.0,
            "recommendation": "Sequential execution recommended",
        }

    # Estimate parallelization potential
    max_concurrent = config["max_concurrent_tasks"]
    estimated_levels = max(1, task_count // max_concurrent)

    # Calculate time savings
    sequential_time = task_count
    parallel_time = estimated_levels
    time_savings_percent = ((sequential_time - parallel_time) / sequential_time) * 100
    speedup_factor = sequential_time / parallel_time

    # Generate recommendation
    if time_savings_percent > 50:
        recommendation = "Excellent parallelization potential"
    elif time_savings_percent > 25:
        recommendation = "Good parallelization potential"
    elif time_savings_percent > 10:
        recommendation = "Modest parallelization potential"
    else:
        recommendation = "Limited parallelization benefit"

    return {
        "parallelization_feasible": True,
        "estimated_time_savings_percent": time_savings_percent,
        "estimated_speedup_factor": speedup_factor,
        "estimated_execution_levels": estimated_levels,
        "max_concurrent_tasks": max_concurrent,
        "recommendation": recommendation,
    }


def create_performance_report(workflow_config: dict[str, Any]) -> str:
    """Create a human-readable performance report.

    Args:
        workflow_config: Workflow configuration with performance estimates

    Returns:
        Formatted performance report string
    """
    if not workflow_config.get("parallelization_feasible", False):
        return "🔄 Sequential execution mode (no parallelization)"

    savings = workflow_config.get("estimated_time_savings_percent", 0)
    speedup = workflow_config.get("estimated_speedup_factor", 1.0)
    levels = workflow_config.get("estimated_execution_levels", 1)
    concurrent = workflow_config.get("max_concurrent_tasks", 1)

    report = f"""⚡ Parallel Execution Optimization Report

📊 Performance Estimates:
   • Time Savings: {savings:.1f}%
   • Speedup Factor: {speedup:.1f}x
   • Execution Levels: {levels}
   • Max Concurrent Tasks: {concurrent}

💡 Recommendation: {workflow_config.get("recommendation", "N/A")}"""

    return report
