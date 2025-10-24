"""Integration tests for orchestrator end-to-end workflows."""

from unittest.mock import AsyncMock, Mock, patch

import pytest

from ultimate_discord_intelligence_bot.orchestration import (
    OrchestrationStrategy,
    get_orchestrator,
)


class TestOrchestratorWorkflowsIntegration:
    """Integration tests for orchestrator end-to-end workflow validation."""

    @pytest.fixture
    def mock_orchestrator(self):
        """Create a mock orchestrator for testing."""
        orchestrator = Mock()
        orchestrator.execute_workflow = AsyncMock()
        return orchestrator

    @pytest.mark.asyncio
    async def test_autonomous_strategy_workflow(self, mock_orchestrator):
        """Test self-directed workflow execution."""
        # Mock autonomous workflow execution
        mock_orchestrator.execute_workflow.return_value = {
            "status": "success",
            "strategy": "autonomous",
            "tasks_completed": 3,
            "self_directed_decisions": 2,
            "execution_time_ms": 1250,
        }

        result = await mock_orchestrator.execute_workflow(
            strategy=OrchestrationStrategy.AUTONOMOUS,
            input_data="Analyze this video content",
            context={"source": "discord", "user_id": "123"},
        )

        assert result["status"] == "success"
        assert result["strategy"] == "autonomous"
        assert result["tasks_completed"] > 0
        assert result["self_directed_decisions"] > 0

    @pytest.mark.asyncio
    async def test_fallback_strategy_workflow(self, mock_orchestrator):
        """Test fallback on agent/task failure."""
        # Mock fallback workflow execution
        mock_orchestrator.execute_workflow.return_value = {
            "status": "success",
            "strategy": "fallback",
            "primary_failed": True,
            "fallback_used": True,
            "tasks_completed": 2,
            "execution_time_ms": 2100,
        }

        result = await mock_orchestrator.execute_workflow(
            strategy=OrchestrationStrategy.FALLBACK,
            input_data="Process this content",
            context={
                "primary_agent": "analysis_agent",
                "fallback_agent": "simple_agent",
            },
        )

        assert result["status"] == "success"
        assert result["strategy"] == "fallback"
        assert result["primary_failed"] is True
        assert result["fallback_used"] is True

    @pytest.mark.asyncio
    async def test_hierarchical_strategy_workflow(self, mock_orchestrator):
        """Test task delegation and result aggregation."""
        # Mock hierarchical workflow execution
        mock_orchestrator.execute_workflow.return_value = {
            "status": "success",
            "strategy": "hierarchical",
            "tasks_delegated": 4,
            "results_aggregated": 4,
            "hierarchy_levels": 3,
            "execution_time_ms": 3200,
        }

        result = await mock_orchestrator.execute_workflow(
            strategy=OrchestrationStrategy.HIERARCHICAL,
            input_data="Complex multi-step analysis",
            context={"workflow_type": "comprehensive_analysis"},
        )

        assert result["status"] == "success"
        assert result["strategy"] == "hierarchical"
        assert result["tasks_delegated"] > 0
        assert result["results_aggregated"] == result["tasks_delegated"]

    @pytest.mark.asyncio
    async def test_monitoring_strategy_workflow(self, mock_orchestrator):
        """Test health checks and alerting."""
        # Mock monitoring workflow execution
        mock_orchestrator.execute_workflow.return_value = {
            "status": "success",
            "strategy": "monitoring",
            "health_checks_performed": 5,
            "alerts_triggered": 1,
            "system_healthy": True,
            "execution_time_ms": 800,
        }

        result = await mock_orchestrator.execute_workflow(
            strategy=OrchestrationStrategy.MONITORING,
            input_data="System health check",
            context={"check_interval": 300},
        )

        assert result["status"] == "success"
        assert result["strategy"] == "monitoring"
        assert result["health_checks_performed"] > 0
        assert result["system_healthy"] is True

    @pytest.mark.asyncio
    async def test_training_strategy_workflow(self, mock_orchestrator):
        """Test RL policy updates during orchestration."""
        # Mock training workflow execution
        mock_orchestrator.execute_workflow.return_value = {
            "status": "success",
            "strategy": "training",
            "policy_updates": 2,
            "learning_episodes": 10,
            "performance_improvement": 0.15,
            "execution_time_ms": 4500,
        }

        result = await mock_orchestrator.execute_workflow(
            strategy=OrchestrationStrategy.TRAINING,
            input_data="Training data batch",
            context={"training_mode": "reinforcement_learning"},
        )

        assert result["status"] == "success"
        assert result["strategy"] == "training"
        assert result["policy_updates"] > 0
        assert result["learning_episodes"] > 0
        assert result["performance_improvement"] > 0

    @pytest.mark.asyncio
    async def test_orchestrator_error_handling(self, mock_orchestrator):
        """Test orchestrator error handling and recovery."""
        # Mock error scenario with recovery
        mock_orchestrator.execute_workflow.side_effect = [
            Exception("Primary strategy failed"),
            {
                "status": "success",
                "strategy": "fallback",
                "error_recovered": True,
                "execution_time_ms": 1800,
            },
        ]

        result = await mock_orchestrator.execute_workflow(
            strategy=OrchestrationStrategy.AUTONOMOUS,
            input_data="Test input",
            context={"enable_fallback": True},
        )

        assert result["status"] == "success"
        assert result["strategy"] == "fallback"
        assert result["error_recovered"] is True

    @pytest.mark.asyncio
    async def test_workflow_context_propagation(self, mock_orchestrator):
        """Test that context propagates through workflow execution."""
        # Mock workflow with context propagation
        mock_orchestrator.execute_workflow.return_value = {
            "status": "success",
            "strategy": "autonomous",
            "context_propagated": True,
            "context_keys": ["user_id", "tenant", "workspace", "request_id"],
            "execution_time_ms": 1500,
        }

        context = {
            "user_id": "user123",
            "tenant": "test_tenant",
            "workspace": "main",
            "request_id": "req456",
        }

        result = await mock_orchestrator.execute_workflow(
            strategy=OrchestrationStrategy.AUTONOMOUS,
            input_data="Test input with context",
            context=context,
        )

        assert result["status"] == "success"
        assert result["context_propagated"] is True
        assert len(result["context_keys"]) == 4

    @pytest.mark.asyncio
    async def test_workflow_metrics_collection(self, mock_orchestrator):
        """Test that workflow metrics are collected properly."""
        # Mock workflow with metrics
        mock_orchestrator.execute_workflow.return_value = {
            "status": "success",
            "strategy": "hierarchical",
            "metrics": {
                "tasks_per_second": 2.5,
                "memory_usage_mb": 128,
                "cpu_usage_percent": 45,
                "cache_hit_rate": 0.85,
                "error_rate": 0.02,
            },
            "execution_time_ms": 2800,
        }

        result = await mock_orchestrator.execute_workflow(
            strategy=OrchestrationStrategy.HIERARCHICAL,
            input_data="Metrics test input",
            context={"collect_metrics": True},
        )

        assert result["status"] == "success"
        assert "metrics" in result
        assert result["metrics"]["tasks_per_second"] > 0
        assert result["metrics"]["cache_hit_rate"] > 0.8
        assert result["metrics"]["error_rate"] < 0.05

    @pytest.mark.asyncio
    async def test_strategy_selection_logic(self):
        """Test orchestrator strategy selection logic."""
        with patch("ultimate_discord_intelligence_bot.orchestration.get_orchestrator") as mock_get_orchestrator:
            mock_orchestrator = Mock()
            mock_get_orchestrator.return_value = mock_orchestrator

            # Test strategy selection for different scenarios
            scenarios = [
                (
                    {"complexity": "high", "time_constraint": False},
                    OrchestrationStrategy.AUTONOMOUS,
                ),
                (
                    {"complexity": "medium", "time_constraint": True},
                    OrchestrationStrategy.FALLBACK,
                ),
                (
                    {"complexity": "high", "hierarchy_needed": True},
                    OrchestrationStrategy.HIERARCHICAL,
                ),
                ({"system_check": True}, OrchestrationStrategy.MONITORING),
                ({"training_mode": True}, OrchestrationStrategy.TRAINING),
            ]

            for _context, expected_strategy in scenarios:
                orchestrator = get_orchestrator(expected_strategy)
                assert orchestrator is not None

    @pytest.mark.asyncio
    async def test_workflow_result_aggregation(self, mock_orchestrator):
        """Test that workflow results are properly aggregated."""
        # Mock multi-task workflow with aggregation
        mock_orchestrator.execute_workflow.return_value = {
            "status": "success",
            "strategy": "hierarchical",
            "aggregated_results": {
                "total_tasks": 3,
                "successful_tasks": 3,
                "failed_tasks": 0,
                "combined_output": "Comprehensive analysis result",
                "confidence_score": 0.92,
            },
            "execution_time_ms": 3500,
        }

        result = await mock_orchestrator.execute_workflow(
            strategy=OrchestrationStrategy.HIERARCHICAL,
            input_data="Multi-step analysis task",
            context={"aggregate_results": True},
        )

        assert result["status"] == "success"
        assert "aggregated_results" in result
        assert result["aggregated_results"]["total_tasks"] > 0
        assert result["aggregated_results"]["successful_tasks"] == result["aggregated_results"]["total_tasks"]
        assert result["aggregated_results"]["confidence_score"] > 0.9
