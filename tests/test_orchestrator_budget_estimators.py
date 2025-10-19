"""Unit tests for orchestrator budget estimators module."""

import pytest

from src.ultimate_discord_intelligence_bot.orchestrator import budget_estimators


class TestBudgetEstimators:
    """Test suite for budget estimation functions."""

    def test_get_budget_limits_standard(self):
        """Test budget limits for standard depth."""
        limits = budget_estimators.get_budget_limits("standard")
        assert limits["max_agents"] == 5
        assert limits["max_tools"] == 10
        assert limits["max_iterations"] == 3
        assert limits["cost_limit_usd"] == 1.0
        assert limits["time_limit_minutes"] == 15
        assert limits["memory_limit_mb"] == 512

    def test_get_budget_limits_deep(self):
        """Test budget limits for deep depth."""
        limits = budget_estimators.get_budget_limits("deep")
        assert limits["max_agents"] == 8
        assert limits["max_tools"] == 20
        assert limits["cost_limit_usd"] == 3.0
        assert limits["time_limit_minutes"] == 30

    def test_get_budget_limits_comprehensive(self):
        """Test budget limits for comprehensive depth."""
        limits = budget_estimators.get_budget_limits("comprehensive")
        assert limits["max_agents"] == 11
        assert limits["cost_limit_usd"] == 5.0
        assert limits["memory_limit_mb"] == 2048

    def test_get_budget_limits_experimental(self):
        """Test budget limits for experimental depth."""
        limits = budget_estimators.get_budget_limits("experimental")
        assert limits["max_agents"] == 15
        assert limits["max_tools"] == 50
        assert limits["cost_limit_usd"] == 10.0
        assert limits["time_limit_minutes"] == 60

    def test_get_budget_limits_invalid_depth(self):
        """Test budget limits with invalid depth defaults to standard."""
        limits = budget_estimators.get_budget_limits("invalid")
        assert limits["max_agents"] == 5  # Should default to standard

    def test_calculate_resource_requirements_standard(self):
        """Test resource requirements for standard depth."""
        reqs = budget_estimators.calculate_resource_requirements("standard")
        assert reqs["cpu_cores"] == 2
        assert reqs["memory_gb"] == 4
        assert reqs["storage_gb"] == 10
        assert reqs["gpu_required"] is False

    def test_calculate_resource_requirements_experimental(self):
        """Test resource requirements for experimental depth."""
        reqs = budget_estimators.calculate_resource_requirements("experimental")
        assert reqs["cpu_cores"] == 8
        assert reqs["memory_gb"] == 32
        assert reqs["gpu_required"] is True

    def test_estimate_workflow_duration_standard(self):
        """Test workflow duration estimates for standard depth."""
        duration = budget_estimators.estimate_workflow_duration("standard")
        assert duration["acquisition"] == 60
        assert duration["transcription"] == 120
        assert duration["analysis"] == 180
        assert duration["total_seconds"] == 480
        assert duration["total_minutes"] == 8

    def test_estimate_workflow_duration_experimental(self):
        """Test workflow duration estimates for experimental depth."""
        duration = budget_estimators.estimate_workflow_duration("experimental")
        assert duration["total_seconds"] == 1680
        assert duration["total_minutes"] == 28

    def test_calculate_cost_estimate_standard(self):
        """Test cost estimation for standard depth."""
        cost = budget_estimators.calculate_cost_estimate("standard")
        assert cost["model"] == "gpt-3.5-turbo"
        assert cost["tokens"]["total"] == 20000
        assert cost["price_per_1k"] == 0.001
        assert cost["estimated_cost"] == pytest.approx(0.02, rel=0.01)

    def test_calculate_cost_estimate_deep(self):
        """Test cost estimation for deep depth."""
        cost = budget_estimators.calculate_cost_estimate("deep")
        assert cost["model"] == "gpt-4"
        assert cost["tokens"]["total"] == 48000
        assert cost["price_per_1k"] == 0.03
        assert cost["estimated_cost"] == pytest.approx(1.44, rel=0.01)

    def test_calculate_cost_estimate_custom_pricing(self):
        """Test cost estimation with custom pricing."""
        custom_pricing = {"gpt-4": 0.05}
        cost = budget_estimators.calculate_cost_estimate("deep", custom_pricing)
        assert cost["price_per_1k"] == 0.05
        assert cost["estimated_cost"] == pytest.approx(2.4, rel=0.01)

    def test_calculate_cost_estimate_breakdown(self):
        """Test cost estimation breakdown by component."""
        cost = budget_estimators.calculate_cost_estimate("standard")
        assert "breakdown" in cost
        assert "transcription" in cost["breakdown"]
        assert "analysis" in cost["breakdown"]
        assert "verification" in cost["breakdown"]
        assert "integration" in cost["breakdown"]

    def test_get_ai_enhancement_level_all_depths(self):
        """Test AI enhancement levels for all depths."""
        assert budget_estimators.get_ai_enhancement_level("standard") == 0.25
        assert budget_estimators.get_ai_enhancement_level("deep") == 0.50
        assert budget_estimators.get_ai_enhancement_level("comprehensive") == 0.75
        assert budget_estimators.get_ai_enhancement_level("experimental") == 1.00

    def test_get_ai_enhancement_level_invalid_depth(self):
        """Test AI enhancement level with invalid depth defaults."""
        assert budget_estimators.get_ai_enhancement_level("invalid") == 0.25
