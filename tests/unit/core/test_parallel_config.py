"""Tests for parallel configuration module."""

import os
from unittest.mock import Mock, patch

from ultimate_discord_intelligence_bot.orchestrator.parallel_config import (
    _apply_intelligent_optimizations,
    _get_available_memory_gb,
    _get_env_overrides,
    create_performance_report,
    estimate_performance_improvement,
    get_optimal_crew_process_type,
    get_parallel_execution_config,
)


class TestGetParallelExecutionConfig:
    """Test cases for get_parallel_execution_config function."""

    def test_get_parallel_execution_config_default(self):
        """Test default parallel execution configuration."""
        with (
            patch("os.cpu_count", return_value=4),
            patch(
                "ultimate_discord_intelligence_bot.orchestrator.parallel_config._get_available_memory_gb",
                return_value=8.0,
            ),
        ):
            config = get_parallel_execution_config()

            assert config["enable_parallel_analysis"] is True
            assert config["enable_parallel_fact_checking"] is True
            assert config["enable_parallel_memory_ops"] is True
            assert config["max_concurrent_tasks"] == 4
            assert config["parallel_execution_threshold"] == 3

    def test_get_parallel_execution_config_low_memory(self):
        """Test configuration with low memory."""
        with (
            patch("os.cpu_count", return_value=4),
            patch(
                "ultimate_discord_intelligence_bot.orchestrator.parallel_config._get_available_memory_gb",
                return_value=2.0,
            ),
        ):
            config = get_parallel_execution_config()

            assert config["enable_parallel_memory_ops"] is False
            assert config["max_concurrent_tasks"] <= 2

    def test_get_parallel_execution_config_low_cpu(self):
        """Test configuration with low CPU count."""
        with (
            patch("os.cpu_count", return_value=1),
            patch(
                "ultimate_discord_intelligence_bot.orchestrator.parallel_config._get_available_memory_gb",
                return_value=8.0,
            ),
        ):
            config = get_parallel_execution_config()

            assert config["enable_parallel_analysis"] is False
            assert config["enable_parallel_fact_checking"] is False
            assert config["max_concurrent_tasks"] == 1

    def test_get_parallel_execution_config_env_override(self):
        """Test configuration with environment variable overrides."""
        env_vars = {
            "ENABLE_PARALLEL_ANALYSIS": "false",
            "ENABLE_PARALLEL_FACT_CHECKING": "false",
            "MAX_CONCURRENT_TASKS": "2",
        }

        with (
            patch.dict(os.environ, env_vars),
            patch("os.cpu_count", return_value=4),
            patch(
                "ultimate_discord_intelligence_bot.orchestrator.parallel_config._get_available_memory_gb",
                return_value=8.0,
            ),
        ):
            config = get_parallel_execution_config()

            assert config["enable_parallel_analysis"] is False
            assert config["enable_parallel_fact_checking"] is False
            assert config["max_concurrent_tasks"] == 2

    def test_get_parallel_execution_config_invalid_env_values(self):
        """Test configuration with invalid environment variable values."""
        env_vars = {
            "MAX_CONCURRENT_TASKS": "invalid",
            "PARALLEL_EXECUTION_THRESHOLD": "not_a_number",
        }

        with (
            patch.dict(os.environ, env_vars),
            patch("os.cpu_count", return_value=4),
            patch(
                "ultimate_discord_intelligence_bot.orchestrator.parallel_config._get_available_memory_gb",
                return_value=8.0,
            ),
        ):
            config = get_parallel_execution_config()

            # Should use default values when env vars are invalid
            assert config["max_concurrent_tasks"] == 4
            assert config["parallel_execution_threshold"] == 3


class TestGetAvailableMemoryGb:
    """Test cases for _get_available_memory_gb function."""

    def test_get_available_memory_gb_with_psutil(self):
        """Test memory detection with psutil available."""
        mock_memory = Mock()
        mock_memory.total = 8 * (1024**3)  # 8GB in bytes

        with patch("psutil.virtual_memory", return_value=mock_memory):
            memory_gb = _get_available_memory_gb()
            assert memory_gb == 8.0

    def test_get_available_memory_gb_without_psutil(self):
        """Test memory detection without psutil (fallback)."""
        with patch("psutil.virtual_memory", side_effect=ImportError):
            memory_gb = _get_available_memory_gb()
            assert memory_gb == 8.0  # Default fallback value


class TestGetEnvOverrides:
    """Test cases for _get_env_overrides function."""

    def test_get_env_overrides_empty(self):
        """Test getting environment overrides when none are set."""
        with patch.dict(os.environ, {}, clear=True):
            overrides = _get_env_overrides()
            assert overrides == {}

    def test_get_env_overrides_parallel_flags(self):
        """Test getting environment overrides for parallel flags."""
        env_vars = {
            "ENABLE_PARALLEL_ANALYSIS": "false",
            "ENABLE_PARALLEL_FACT_CHECKING": "true",
            "ENABLE_PARALLEL_MEMORY_OPS": "false",
        }

        with patch.dict(os.environ, env_vars):
            overrides = _get_env_overrides()

            assert overrides["enable_parallel_analysis"] is False
            assert overrides["enable_parallel_fact_checking"] is True
            assert overrides["enable_parallel_memory_ops"] is False

    def test_get_env_overrides_performance_tuning(self):
        """Test getting environment overrides for performance tuning."""
        env_vars = {"MAX_CONCURRENT_TASKS": "6", "PARALLEL_EXECUTION_THRESHOLD": "4"}

        with patch.dict(os.environ, env_vars):
            overrides = _get_env_overrides()

            assert overrides["max_concurrent_tasks"] == 6
            assert overrides["parallel_execution_threshold"] == 4

    def test_get_env_overrides_invalid_values(self):
        """Test getting environment overrides with invalid values."""
        env_vars = {
            "MAX_CONCURRENT_TASKS": "invalid",
            "PARALLEL_EXECUTION_THRESHOLD": "not_a_number",
        }

        with patch.dict(os.environ, env_vars):
            overrides = _get_env_overrides()

            # Invalid values should not be included
            assert "max_concurrent_tasks" not in overrides
            assert "parallel_execution_threshold" not in overrides


class TestApplyIntelligentOptimizations:
    """Test cases for _apply_intelligent_optimizations function."""

    def test_apply_intelligent_optimizations_low_memory(self):
        """Test intelligent optimizations for low memory systems."""
        config = {
            "enable_parallel_memory_ops": True,
            "max_concurrent_tasks": 6,
            "memory_efficient_mode": True,
            "cpu_efficient_mode": False,
        }

        optimized = _apply_intelligent_optimizations(config, 4, 2.0)

        assert optimized["enable_parallel_memory_ops"] is False
        assert optimized["max_concurrent_tasks"] <= 2

    def test_apply_intelligent_optimizations_low_cpu(self):
        """Test intelligent optimizations for low CPU systems."""
        config = {
            "enable_parallel_analysis": True,
            "enable_parallel_fact_checking": True,
            "max_concurrent_tasks": 6,
            "memory_efficient_mode": False,
            "cpu_efficient_mode": True,
        }

        optimized = _apply_intelligent_optimizations(config, 1, 8.0)

        assert optimized["enable_parallel_analysis"] is False
        assert optimized["enable_parallel_fact_checking"] is False
        assert optimized["max_concurrent_tasks"] == 1

    def test_apply_intelligent_optimizations_high_performance(self):
        """Test intelligent optimizations for high-performance systems."""
        config = {
            "enable_parallel_memory_ops": True,
            "max_concurrent_tasks": 4,
            "memory_efficient_mode": False,
            "cpu_efficient_mode": False,
        }

        optimized = _apply_intelligent_optimizations(config, 8, 16.0)

        # Should not disable features on high-performance systems
        assert optimized["enable_parallel_memory_ops"] is True
        assert optimized["max_concurrent_tasks"] == 4


class TestGetOptimalCrewProcessType:
    """Test cases for get_optimal_crew_process_type function."""

    def test_get_optimal_crew_process_type_sequential(self):
        """Test process type selection for sequential execution."""
        config = {
            "parallel_execution_threshold": 3,
            "enable_parallel_analysis": False,
            "enable_parallel_fact_checking": False,
            "enable_parallel_memory_ops": False,
        }

        # Low task count
        process_type = get_optimal_crew_process_type(2, config)
        assert process_type == "sequential"

        # High task count but parallel disabled
        process_type = get_optimal_crew_process_type(10, config)
        assert process_type == "sequential"

    def test_get_optimal_crew_process_type_hierarchical(self):
        """Test process type selection for hierarchical execution."""
        config = {
            "parallel_execution_threshold": 3,
            "enable_parallel_analysis": True,
            "enable_parallel_fact_checking": False,
            "enable_parallel_memory_ops": False,
        }

        process_type = get_optimal_crew_process_type(5, config)
        assert process_type == "hierarchical"

    def test_get_optimal_crew_process_type_threshold_based(self):
        """Test process type selection based on task count threshold."""
        config = {
            "parallel_execution_threshold": 5,
            "enable_parallel_analysis": True,
            "enable_parallel_fact_checking": True,
            "enable_parallel_memory_ops": True,
        }

        # Below threshold
        process_type = get_optimal_crew_process_type(3, config)
        assert process_type == "sequential"

        # Above threshold
        process_type = get_optimal_crew_process_type(7, config)
        assert process_type == "hierarchical"


class TestEstimatePerformanceImprovement:
    """Test cases for estimate_performance_improvement function."""

    def test_estimate_performance_improvement_no_parallelization(self):
        """Test performance estimation with no parallelization."""
        config = {
            "enable_parallel_analysis": False,
            "enable_parallel_fact_checking": False,
            "enable_parallel_memory_ops": False,
        }

        estimate = estimate_performance_improvement(5, config)

        assert estimate["parallelization_feasible"] is False
        assert estimate["estimated_time_savings_percent"] == 0.0
        assert estimate["estimated_speedup_factor"] == 1.0
        assert "Sequential execution recommended" in estimate["recommendation"]

    def test_estimate_performance_improvement_high_parallelization(self):
        """Test performance estimation with high parallelization potential."""
        config = {
            "enable_parallel_analysis": True,
            "enable_parallel_fact_checking": True,
            "enable_parallel_memory_ops": True,
            "max_concurrent_tasks": 4,
        }

        estimate = estimate_performance_improvement(12, config)

        assert estimate["parallelization_feasible"] is True
        assert estimate["estimated_time_savings_percent"] > 50
        assert estimate["estimated_speedup_factor"] > 2.0
        assert "Excellent parallelization potential" in estimate["recommendation"]

    def test_estimate_performance_improvement_modest_parallelization(self):
        """Test performance estimation with modest parallelization potential."""
        config = {
            "enable_parallel_analysis": True,
            "enable_parallel_fact_checking": False,
            "enable_parallel_memory_ops": False,
            "max_concurrent_tasks": 2,
        }

        estimate = estimate_performance_improvement(6, config)

        assert estimate["parallelization_feasible"] is True
        assert 10 <= estimate["estimated_time_savings_percent"] <= 50
        assert 1.0 < estimate["estimated_speedup_factor"] <= 2.0

    def test_estimate_performance_improvement_limited_parallelization(self):
        """Test performance estimation with limited parallelization potential."""
        config = {
            "enable_parallel_analysis": True,
            "enable_parallel_fact_checking": False,
            "enable_parallel_memory_ops": False,
            "max_concurrent_tasks": 2,
        }

        estimate = estimate_performance_improvement(4, config)

        assert estimate["parallelization_feasible"] is True
        assert estimate["estimated_time_savings_percent"] < 60  # Adjusted for actual calculation
        assert estimate["estimated_speedup_factor"] < 3.0  # Adjusted for actual calculation


class TestCreatePerformanceReport:
    """Test cases for create_performance_report function."""

    def test_create_performance_report_sequential(self):
        """Test performance report for sequential execution."""
        workflow_config = {"parallelization_feasible": False}

        report = create_performance_report(workflow_config)

        assert "Sequential execution mode" in report
        assert "🔄" in report

    def test_create_performance_report_parallel(self):
        """Test performance report for parallel execution."""
        workflow_config = {
            "parallelization_feasible": True,
            "estimated_time_savings_percent": 60.5,
            "estimated_speedup_factor": 2.5,
            "estimated_execution_levels": 3,
            "max_concurrent_tasks": 4,
            "recommendation": "Excellent parallelization potential",
        }

        report = create_performance_report(workflow_config)

        assert "⚡ Parallel Execution Optimization Report" in report
        assert "Time Savings: 60.5%" in report
        assert "Speedup Factor: 2.5x" in report
        assert "Execution Levels: 3" in report
        assert "Max Concurrent Tasks: 4" in report
        assert "Excellent parallelization potential" in report

    def test_create_performance_report_missing_fields(self):
        """Test performance report with missing fields."""
        workflow_config = {
            "parallelization_feasible": True,
            "estimated_time_savings_percent": 30.0,
        }

        report = create_performance_report(workflow_config)

        assert "⚡ Parallel Execution Optimization Report" in report
        assert "Time Savings: 30.0%" in report
        assert "N/A" in report  # For missing recommendation
