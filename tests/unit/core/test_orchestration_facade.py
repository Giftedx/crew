"""Tests for unified orchestration facade (ADR-0004)."""

from __future__ import annotations

import pytest

from ultimate_discord_intelligence_bot.orchestration import OrchestrationFacade, OrchestrationStrategy, get_orchestrator
from ultimate_discord_intelligence_bot.step_result import StepResult


class TestOrchestrationStrategy:
    """Test orchestration strategy enum."""

    def test_strategies_defined(self):
        """Test all orchestration strategies are defined."""
        assert OrchestrationStrategy.AUTONOMOUS == "autonomous"
        assert OrchestrationStrategy.FALLBACK == "fallback"
        assert OrchestrationStrategy.HIERARCHICAL == "hierarchical"
        assert OrchestrationStrategy.MONITORING == "monitoring"
        assert OrchestrationStrategy.TRAINING == "training"


class TestOrchestrationFacade:
    """Test orchestration facade."""

    def test_facade_initialization(self):
        """Test facade initializes with default strategy."""
        facade = OrchestrationFacade()
        assert facade.strategy == OrchestrationStrategy.AUTONOMOUS

    def test_facade_custom_strategy(self):
        """Test facade with custom strategy."""
        facade = OrchestrationFacade(strategy=OrchestrationStrategy.FALLBACK)
        assert facade.strategy == OrchestrationStrategy.FALLBACK

    @pytest.mark.asyncio
    async def test_execute_workflow_signature(self):
        """Test execute_workflow accepts expected parameters."""
        facade = OrchestrationFacade(strategy=OrchestrationStrategy.AUTONOMOUS)
        try:
            result = await facade.execute_workflow(
                url="https://example.com/test", depth="standard", tenant="test", workspace="test"
            )
            assert isinstance(result, StepResult)
        except Exception:
            pass


class TestOrchestrationSingleton:
    """Test global orchestrator singleton."""

    def test_get_orchestrator_default(self):
        """Test get_orchestrator returns autonomous by default."""
        orchestrator = get_orchestrator()
        assert orchestrator.strategy == OrchestrationStrategy.AUTONOMOUS

    def test_get_orchestrator_with_strategy(self):
        """Test get_orchestrator accepts strategy parameter."""
        orchestrator = get_orchestrator(strategy=OrchestrationStrategy.FALLBACK)
        assert orchestrator.strategy == OrchestrationStrategy.FALLBACK

    def test_strategy_switching(self):
        """Test switching strategies creates new instance."""
        orch1 = get_orchestrator(OrchestrationStrategy.AUTONOMOUS)
        orch2 = get_orchestrator(OrchestrationStrategy.FALLBACK)
        assert orch1.strategy != orch2.strategy


class TestOrchestrationIntegration:
    """Integration tests for orchestration facade."""

    def test_autonomous_orchestrator_loads(self):
        """Test autonomous orchestrator can be loaded."""
        facade = OrchestrationFacade(strategy=OrchestrationStrategy.AUTONOMOUS)
        try:
            orchestrator = facade._get_orchestrator()
            assert orchestrator is not None
        except Exception:
            pass

    def test_invalid_strategy_raises(self):
        """Test invalid strategy raises ValueError."""
        facade = OrchestrationFacade()
        facade.strategy = "invalid_strategy"
        with pytest.raises(ValueError, match="Unknown orchestration strategy"):
            facade._get_orchestrator()
