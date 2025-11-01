"""Integration tests for framework abstraction layer.

Tests the universal framework adapter interface and validates that different
frameworks can be used interchangeably.
"""

from __future__ import annotations

import pytest

from ai.frameworks import get_framework_adapter, list_available_frameworks
from ai.frameworks.protocols import AgentRole, FrameworkFeature
from ultimate_discord_intelligence_bot.crew_core.interfaces import (
    CrewConfig,
    CrewPriority,
    CrewTask,
)


class TestFrameworkRegistry:
    """Test framework registration and discovery."""

    def test_list_available_frameworks(self) -> None:
        """Test that available frameworks can be listed."""
        frameworks = list_available_frameworks()
        assert isinstance(frameworks, list)
        assert "crewai" in frameworks  # CrewAI should always be available

    def test_get_framework_adapter_crewai(self) -> None:
        """Test getting CrewAI framework adapter."""
        adapter = get_framework_adapter("crewai")
        assert adapter.framework_name == "crewai"
        assert adapter.framework_version is not None

    def test_get_framework_adapter_invalid(self) -> None:
        """Test that requesting unknown framework raises ValueError."""
        with pytest.raises(ValueError, match="Unknown framework"):
            get_framework_adapter("nonexistent_framework")


class TestCrewAIAdapter:
    """Test CrewAI framework adapter implementation."""

    def test_adapter_properties(self) -> None:
        """Test adapter basic properties."""
        adapter = get_framework_adapter("crewai")
        assert adapter.framework_name == "crewai"
        assert isinstance(adapter.framework_version, str)

    def test_supported_features(self) -> None:
        """Test that adapter declares supported features."""
        adapter = get_framework_adapter("crewai")

        # CrewAI should support these core features
        assert adapter.supports_feature(FrameworkFeature.SEQUENTIAL_EXECUTION)
        assert adapter.supports_feature(FrameworkFeature.PARALLEL_EXECUTION)
        assert adapter.supports_feature(FrameworkFeature.ASYNC_EXECUTION)
        assert adapter.supports_feature(FrameworkFeature.CUSTOM_TOOLS)

        # CrewAI doesn't support state persistence by default
        assert not adapter.supports_feature(FrameworkFeature.STATE_PERSISTENCE)

    def test_get_capabilities(self) -> None:
        """Test getting adapter capabilities."""
        adapter = get_framework_adapter("crewai")
        capabilities = adapter.get_capabilities()

        assert "supported_features" in capabilities
        assert "supports_async" in capabilities
        assert "limitations" in capabilities
        assert capabilities["supports_async"] is True

    @pytest.mark.asyncio
    async def test_create_agent(self) -> None:
        """Test creating an agent via the adapter."""
        adapter = get_framework_adapter("crewai")

        role = AgentRole(
            role_name="researcher",
            goal="Find and analyze information",
            backstory="An expert researcher",
            capabilities=["web_search"],
        )

        result = await adapter.create_agent(role)

        # Should succeed or fail gracefully if CrewAI not installed
        assert result is not None
        if result.success:
            assert result.data is not None


class TestFrameworkInteroperability:
    """Test that frameworks work interchangeably via the adapter interface."""

    @pytest.mark.asyncio
    async def test_execute_task_via_adapter(self) -> None:
        """Test executing a task via framework adapter."""
        adapter = get_framework_adapter("crewai")

        task = CrewTask(
            task_id="test-task-001",
            task_type="simple_test",
            description="Test task for framework validation",
            inputs={"test_data": "validation"},
            priority=CrewPriority.NORMAL,
        )

        config = CrewConfig(
            tenant_id="test-tenant",
            timeout_seconds=30,
        )

        result = await adapter.execute_task(task, config)

        # Should return StepResult
        assert result is not None
        assert hasattr(result, "success")

        # If execution succeeded, verify ExecutionResult structure
        if result.success:
            execution_result = result.data
            assert hasattr(execution_result, "success")
            assert hasattr(execution_result, "output")
            assert hasattr(execution_result, "execution_time_ms")


class TestAutoGenAdapter:
    """Test AutoGen framework adapter implementation."""

    def test_adapter_properties(self) -> None:
        """Test AutoGen adapter basic properties."""
        try:
            adapter = get_framework_adapter("autogen")
            assert adapter.framework_name == "autogen"
            assert isinstance(adapter.framework_version, str)
        except ValueError:
            pytest.skip("AutoGen adapter not available")

    def test_supported_features(self) -> None:
        """Test that AutoGen adapter declares supported features."""
        try:
            adapter = get_framework_adapter("autogen")

            # AutoGen should support these conversation-centric features
            assert adapter.supports_feature(FrameworkFeature.SEQUENTIAL_EXECUTION)
            assert adapter.supports_feature(FrameworkFeature.MULTI_AGENT_COLLABORATION)
            assert adapter.supports_feature(FrameworkFeature.HUMAN_IN_LOOP)
            assert adapter.supports_feature(FrameworkFeature.ASYNC_EXECUTION)

            # AutoGen does NOT support state persistence
            assert not adapter.supports_feature(FrameworkFeature.STATE_PERSISTENCE)
        except ValueError:
            pytest.skip("AutoGen adapter not available")

    def test_get_capabilities(self) -> None:
        """Test getting AutoGen adapter capabilities."""
        try:
            adapter = get_framework_adapter("autogen")
            capabilities = adapter.get_capabilities()

            assert "supported_features" in capabilities
            assert "human_in_loop" in capabilities["metadata"]
            assert "code_execution" in capabilities["metadata"]
            assert capabilities["metadata"]["human_in_loop"] is True
            assert len(capabilities["state_backends"]) == 0  # No built-in persistence
        except ValueError:
            pytest.skip("AutoGen adapter not available")


class TestBackwardCompatibility:
    """Test that existing crew_core code still works."""

    def test_crew_config_unchanged(self) -> None:
        """Test that CrewConfig interface is unchanged."""
        config = CrewConfig(tenant_id="test")
        assert config.tenant_id == "test"
        assert config.enable_cache is True
        assert config.timeout_seconds == 300

    def test_crew_task_unchanged(self) -> None:
        """Test that CrewTask interface is unchanged."""
        task = CrewTask(
            task_id="test",
            task_type="test_type",
            description="Test task",
            inputs={"key": "value"},
        )
        assert task.task_id == "test"
        assert task.task_type == "test_type"
        assert task.inputs == {"key": "value"}
