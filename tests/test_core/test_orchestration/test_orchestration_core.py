"""Tests for core orchestration system."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest


# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "src"))

from core.orchestration import (
    BaseOrchestrator,
    OrchestrationContext,
    OrchestrationLayer,
    OrchestrationType,
    get_orchestration_facade,
)
from ultimate_discord_intelligence_bot.step_result import StepResult


class TestOrchestrator(BaseOrchestrator):
    """Test orchestrator for unit tests."""

    def __init__(
        self,
        name: str = "test_orchestrator",
        layer: OrchestrationLayer = OrchestrationLayer.APPLICATION,
    ) -> None:
        super().__init__(
            layer=layer,
            name=name,
            orchestration_type=OrchestrationType.SEQUENTIAL,
        )
        self.orchestrate_called = False
        self.cleanup_called = False

    async def orchestrate(
        self,
        context: OrchestrationContext,
        **kwargs,
    ) -> StepResult:
        """Test orchestration."""
        self.orchestrate_called = True
        self._log_orchestration_start(context)

        result = StepResult.ok(data={"test": "data", "request_id": context.request_id})

        self._log_orchestration_end(context, result)
        return result

    async def cleanup(self) -> None:
        """Test cleanup."""
        self.cleanup_called = True


class TestOrchestrationContext:
    """Tests for OrchestrationContext."""

    def test_context_creation(self):
        """Test creating a context."""
        context = OrchestrationContext(
            tenant_id="test_tenant",
            request_id="req-123",
            metadata={"key": "value"},
            trace_id="trace-456",
        )

        assert context.tenant_id == "test_tenant"
        assert context.request_id == "req-123"
        assert context.metadata == {"key": "value"}
        assert context.trace_id == "trace-456"
        assert context.parent_orchestrator is None
        assert context.orchestration_depth == 0

    def test_child_context_creation(self):
        """Test creating a child context."""
        parent_context = OrchestrationContext(
            tenant_id="test_tenant",
            request_id="req-123",
            metadata={"key": "value"},
        )

        child_context = parent_context.create_child_context("parent_orch")

        assert child_context.tenant_id == parent_context.tenant_id
        assert child_context.request_id == parent_context.request_id
        assert child_context.metadata == parent_context.metadata
        assert child_context.parent_orchestrator == "parent_orch"
        assert child_context.orchestration_depth == 1

    def test_metadata_copied_to_child(self):
        """Test that metadata is copied, not shared."""
        parent_context = OrchestrationContext(
            tenant_id="test_tenant",
            request_id="req-123",
            metadata={"key": "value"},
        )

        child_context = parent_context.create_child_context("parent")
        child_context.metadata["new_key"] = "new_value"

        assert "new_key" not in parent_context.metadata


class TestBaseOrchestrator:
    """Tests for BaseOrchestrator."""

    def test_orchestrator_initialization(self):
        """Test orchestrator initialization."""
        orch = TestOrchestrator(
            name="test",
            layer=OrchestrationLayer.DOMAIN,
        )

        assert orch.name == "test"
        assert orch.layer == OrchestrationLayer.DOMAIN
        assert orch.orchestration_type == OrchestrationType.SEQUENTIAL

    @pytest.mark.asyncio
    async def test_orchestrator_execution(self):
        """Test orchestrator execution."""
        orch = TestOrchestrator()
        context = OrchestrationContext(
            tenant_id="test",
            request_id="req-123",
        )

        result = await orch.orchestrate(context)

        assert result.success
        assert orch.orchestrate_called
        assert result.data["request_id"] == "req-123"

    @pytest.mark.asyncio
    async def test_orchestrator_cleanup(self):
        """Test orchestrator cleanup."""
        orch = TestOrchestrator()

        await orch.cleanup()

        assert orch.cleanup_called


class TestOrchestrationFacade:
    """Tests for OrchestrationFacade."""

    def test_singleton_facade(self):
        """Test that get_orchestration_facade returns singleton."""
        facade1 = get_orchestration_facade()
        facade2 = get_orchestration_facade()

        assert facade1 is facade2

    def test_register_orchestrator(self):
        """Test registering an orchestrator."""
        from core.orchestration.facade import OrchestrationFacade

        facade = OrchestrationFacade()
        orch = TestOrchestrator(name="test_reg")

        facade.register(orch)

        assert facade.get("test_reg") is orch

    def test_register_duplicate_raises(self):
        """Test that registering duplicate name raises."""
        from core.orchestration.facade import OrchestrationFacade

        facade = OrchestrationFacade()
        orch1 = TestOrchestrator(name="duplicate")
        orch2 = TestOrchestrator(name="duplicate")

        facade.register(orch1)

        with pytest.raises(ValueError, match="already registered"):
            facade.register(orch2)

    def test_unregister_orchestrator(self):
        """Test unregistering an orchestrator."""
        from core.orchestration.facade import OrchestrationFacade

        facade = OrchestrationFacade()
        orch = TestOrchestrator(name="test_unreg")

        facade.register(orch)
        facade.unregister("test_unreg")

        assert facade.get("test_unreg") is None

    def test_unregister_nonexistent_raises(self):
        """Test that unregistering nonexistent orchestrator raises."""
        from core.orchestration.facade import OrchestrationFacade

        facade = OrchestrationFacade()

        with pytest.raises(KeyError, match="not registered"):
            facade.unregister("nonexistent")

    def test_get_by_layer(self):
        """Test getting orchestrators by layer."""
        from core.orchestration.facade import OrchestrationFacade

        facade = OrchestrationFacade()
        orch1 = TestOrchestrator(name="app1", layer=OrchestrationLayer.APPLICATION)
        orch2 = TestOrchestrator(name="app2", layer=OrchestrationLayer.APPLICATION)
        orch3 = TestOrchestrator(name="domain1", layer=OrchestrationLayer.DOMAIN)

        facade.register(orch1)
        facade.register(orch2)
        facade.register(orch3)

        app_orchs = facade.get_by_layer(OrchestrationLayer.APPLICATION)

        assert len(app_orchs) == 2
        assert orch1 in app_orchs
        assert orch2 in app_orchs
        assert orch3 not in app_orchs

    @pytest.mark.asyncio
    async def test_orchestrate_success(self):
        """Test successful orchestration through facade."""
        from core.orchestration.facade import OrchestrationFacade

        facade = OrchestrationFacade()
        orch = TestOrchestrator(name="test_exec")
        facade.register(orch)

        context = OrchestrationContext(
            tenant_id="test",
            request_id="req-123",
        )

        result = await facade.orchestrate("test_exec", context)

        assert result.success
        assert orch.orchestrate_called
        assert orch.cleanup_called

    @pytest.mark.asyncio
    async def test_orchestrate_not_found(self):
        """Test orchestration with nonexistent orchestrator."""
        from core.orchestration.facade import OrchestrationFacade

        facade = OrchestrationFacade()
        context = OrchestrationContext(
            tenant_id="test",
            request_id="req-123",
        )

        result = await facade.orchestrate("nonexistent", context)

        assert not result.success

    @pytest.mark.asyncio
    async def test_orchestrate_cleanup_on_error(self):
        """Test that cleanup is called even when orchestration fails."""
        from core.orchestration.facade import OrchestrationFacade

        class FailingOrchestrator(TestOrchestrator):
            async def orchestrate(self, context, **kwargs):
                self.orchestrate_called = True
                raise RuntimeError("Test error")

        facade = OrchestrationFacade()
        orch = FailingOrchestrator(name="failing")
        facade.register(orch)

        context = OrchestrationContext(
            tenant_id="test",
            request_id="req-123",
        )

        result = await facade.orchestrate("failing", context)

        assert not result.success
        assert orch.orchestrate_called
        assert orch.cleanup_called

    def test_list_orchestrators(self):
        """Test listing all orchestrators."""
        from core.orchestration.facade import OrchestrationFacade

        facade = OrchestrationFacade()
        orch1 = TestOrchestrator(name="orch1", layer=OrchestrationLayer.DOMAIN)
        orch2 = TestOrchestrator(name="orch2", layer=OrchestrationLayer.APPLICATION)

        facade.register(orch1)
        facade.register(orch2)

        orchestrators = facade.list_orchestrators()

        assert len(orchestrators) == 2
        assert orchestrators["orch1"]["layer"] == "domain"
        assert orchestrators["orch2"]["layer"] == "application"
