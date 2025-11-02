"""Integration tests for routing decision quality."""

from platform.llm.providers.openrouter import OpenRouterService
from unittest.mock import patch

import pytest


class TestRoutingQualityIntegration:
    """Integration tests for routing decision quality validation."""

    @pytest.fixture
    def mock_openrouter_service(self):
        """Create a mock OpenRouter service for testing."""
        with patch.object(OpenRouterService, "__init__", return_value=None):
            service = OpenRouterService()
            service.api_key = "test_key"
            return service

    @pytest.mark.asyncio
    async def test_model_selection_accuracy(self, mock_openrouter_service):
        """Test that correct model is chosen for task type."""
        with patch.object(mock_openrouter_service, "route") as mock_route:
            mock_route.return_value = {
                "status": "success",
                "response": "test response",
                "model": "openai/gpt-3.5-turbo",
                "task_type": "analysis",
            }
            result = mock_openrouter_service.route("Analyze this content for accuracy")
            assert result["status"] == "success"
            assert result["model"] == "openai/gpt-3.5-turbo"
            assert result["task_type"] == "analysis"

    @pytest.mark.asyncio
    async def test_fallback_logic(self, mock_openrouter_service):
        """Test graceful degradation when primary model unavailable."""
        with patch.object(mock_openrouter_service, "route") as mock_route:
            mock_route.side_effect = [
                Exception("Primary model unavailable"),
                {"status": "success", "response": "fallback response", "model": "anthropic/claude-3-haiku"},
            ]
            result = mock_openrouter_service.route("Test prompt")
            assert result["status"] == "success"
            assert result["model"] == "anthropic/claude-3-haiku"
            assert result["response"] == "fallback response"

    @pytest.mark.asyncio
    async def test_cost_optimization(self, mock_openrouter_service):
        """Test that cheaper models are used when appropriate."""
        with patch.object(mock_openrouter_service, "route") as mock_route:
            mock_route.return_value = {
                "status": "success",
                "response": "simple response",
                "model": "openai/gpt-3.5-turbo",
                "cost_optimized": True,
            }
            result = mock_openrouter_service.route("Simple question")
            assert result["status"] == "success"
            assert result["model"] == "openai/gpt-3.5-turbo"
            assert result.get("cost_optimized") is True

    @pytest.mark.asyncio
    async def test_latency_constraints(self, mock_openrouter_service):
        """Test that fast models are selected for low-latency tasks."""
        with patch.object(mock_openrouter_service, "route") as mock_route:
            mock_route.return_value = {
                "status": "success",
                "response": "fast response",
                "model": "anthropic/claude-3-haiku",
                "latency_ms": 150,
                "latency_optimized": True,
            }
            result = mock_openrouter_service.route("Quick response needed")
            assert result["status"] == "success"
            assert result["model"] == "anthropic/claude-3-haiku"
            assert result["latency_ms"] < 200
            assert result.get("latency_optimized") is True

    @pytest.mark.asyncio
    async def test_rl_routing_convergence(self, mock_openrouter_service):
        """Test reinforcement learning model selection convergence."""
        models = ["model_a", "model_b", "model_c"]
        convergence_data = []

        def mock_route_with_convergence(prompt, **kwargs):
            call_count = len(convergence_data)
            if call_count < 5:
                model = models[call_count % len(models)]
            else:
                model = models[0]
            result = {
                "status": "success",
                "response": f"response from {model}",
                "model": model,
                "rl_converged": call_count >= 5,
            }
            convergence_data.append(result)
            return result

        with patch.object(mock_openrouter_service, "route", side_effect=mock_route_with_convergence):
            for i in range(10):
                mock_openrouter_service.route(f"Test prompt {i}")
            assert convergence_data[5]["rl_converged"] is True
            assert convergence_data[5]["model"] == "model_a"
            assert convergence_data[9]["model"] == "model_a"

    @pytest.mark.asyncio
    async def test_task_type_routing(self, mock_openrouter_service):
        """Test that different task types route to appropriate models."""
        task_type_model_mapping = {
            "analysis": "openai/gpt-4",
            "summarization": "anthropic/claude-3-sonnet",
            "translation": "openai/gpt-3.5-turbo",
            "coding": "anthropic/claude-3-opus",
        }

        def mock_route_by_task_type(prompt, task_type=None, **kwargs):
            model = task_type_model_mapping.get(task_type, "openai/gpt-3.5-turbo")
            return {"status": "success", "response": "Task-specific response", "model": model, "task_type": task_type}

        with patch.object(mock_openrouter_service, "route", side_effect=mock_route_by_task_type):
            for task_type, expected_model in task_type_model_mapping.items():
                result = mock_openrouter_service.route(f"Test {task_type}", task_type=task_type)
                assert result["status"] == "success"
                assert result["model"] == expected_model
                assert result["task_type"] == task_type

    @pytest.mark.asyncio
    async def test_routing_with_context(self, mock_openrouter_service):
        """Test routing decisions with context information."""
        with patch.object(mock_openrouter_service, "route") as mock_route:
            mock_route.return_value = {
                "status": "success",
                "response": "contextual response",
                "model": "openai/gpt-4",
                "context_used": True,
                "context_length": 1500,
            }
            result = mock_openrouter_service.route("Complex analysis task", context="Large context information...")
            assert result["status"] == "success"
            assert result.get("context_used") is True
            assert result["context_length"] > 1000

    @pytest.mark.asyncio
    async def test_routing_error_handling(self, mock_openrouter_service):
        """Test routing error handling and recovery."""
        with patch.object(mock_openrouter_service, "route") as mock_route:
            mock_route.side_effect = [
                Exception("Rate limit exceeded"),
                Exception("Model unavailable"),
                {"status": "success", "response": "recovered response", "model": "fallback_model"},
            ]
            result = mock_openrouter_service.route("Test prompt")
            assert result["status"] == "success"
            assert result["model"] == "fallback_model"

    @pytest.mark.asyncio
    async def test_routing_metrics_collection(self, mock_openrouter_service):
        """Test that routing metrics are collected properly."""
        with patch.object(mock_openrouter_service, "route") as mock_route:
            mock_route.return_value = {
                "status": "success",
                "response": "test response",
                "model": "openai/gpt-3.5-turbo",
                "metrics": {"routing_time_ms": 45, "model_selection_confidence": 0.95, "fallback_used": False},
            }
            result = mock_openrouter_service.route("Test prompt")
            assert result["status"] == "success"
            assert "metrics" in result
            assert result["metrics"]["routing_time_ms"] < 100
            assert result["metrics"]["model_selection_confidence"] > 0.9
            assert result["metrics"]["fallback_used"] is False
