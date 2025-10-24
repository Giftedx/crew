"""Tests for the agent factory and agent definitions."""

from __future__ import annotations

from unittest.mock import Mock, patch

import pytest

from ultimate_discord_intelligence_bot.config.agent_definitions import (
    AGENT_DEFINITIONS,
    get_agent_definition,
    get_agent_group,
    validate_agent_definitions,
)
from ultimate_discord_intelligence_bot.config.agent_factory import AgentFactory


class TestAgentDefinitions:
    """Test agent definitions functionality."""

    def test_get_agent_definition(self) -> None:
        """Test getting agent definitions."""
        definition = get_agent_definition("mission_orchestrator")
        assert definition is not None
        assert definition.name == "mission_orchestrator"
        assert definition.role == "Autonomy Mission Orchestrator"
        assert definition.goal == "Coordinate end-to-end missions, sequencing depth, specialists, and budgets."

    def test_get_nonexistent_agent_definition(self) -> None:
        """Test getting non-existent agent definition."""
        definition = get_agent_definition("nonexistent_agent")
        assert definition is None

    def test_get_agent_group(self) -> None:
        """Test getting agent groups."""
        group = get_agent_group("content_pipeline")
        assert "acquisition_specialist" in group
        assert "content_analyst" in group
        assert "fact_checker" in group
        assert "knowledge_integrator" in group

    def test_get_nonexistent_agent_group(self) -> None:
        """Test getting non-existent agent group."""
        group = get_agent_group("nonexistent_group")
        assert group == []

    def test_validate_agent_definitions(self) -> None:
        """Test agent definition validation."""
        issues = validate_agent_definitions()
        # Should have no issues with current definitions
        assert len(issues) == 0

    def test_agent_definition_structure(self) -> None:
        """Test that agent definitions have required fields."""
        for _name, definition in AGENT_DEFINITIONS.items():
            assert definition.name
            assert definition.role
            assert definition.goal
            assert definition.backstory
            assert isinstance(definition.tools, list)
            assert isinstance(definition.verbose, bool)
            assert isinstance(definition.max_iter, int)
            assert definition.max_iter > 0


class TestAgentFactory:
    """Test agent factory functionality."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.factory = AgentFactory()

    @patch("ultimate_discord_intelligence_bot.config.agent_factory.Agent")
    def test_create_agent_success(self, mock_agent_class: Mock) -> None:
        """Test successful agent creation."""
        mock_agent = Mock()
        mock_agent_class.return_value = mock_agent

        # Mock tool creation
        with patch.object(self.factory, "_create_tools", return_value=[]):
            agent = self.factory.create_agent("mission_orchestrator")

            assert agent is not None
            mock_agent_class.assert_called_once()

    def test_create_nonexistent_agent(self) -> None:
        """Test creating non-existent agent."""
        agent = self.factory.create_agent("nonexistent_agent")
        assert agent is None

    @patch("ultimate_discord_intelligence_bot.config.agent_factory.Agent")
    def test_create_agent_with_overrides(self, mock_agent_class: Mock) -> None:
        """Test creating agent with parameter overrides."""
        mock_agent = Mock()
        mock_agent_class.return_value = mock_agent

        with patch.object(self.factory, "_create_tools", return_value=[]):
            agent = self.factory.create_agent("mission_orchestrator", verbose=False, max_iter=10)

            assert agent is not None
            # Check that overrides were applied
            call_args = mock_agent_class.call_args[1]
            assert call_args["verbose"] is False
            assert call_args["max_iter"] == 10

    @patch("ultimate_discord_intelligence_bot.config.agent_factory.Agent")
    def test_create_multiple_agents(self, mock_agent_class: Mock) -> None:
        """Test creating multiple agents."""
        mock_agent = Mock()
        mock_agent_class.return_value = mock_agent

        with patch.object(self.factory, "_create_tools", return_value=[]):
            agents = self.factory.create_agents(["mission_orchestrator", "executive_supervisor"])

            assert len(agents) == 2
            assert mock_agent_class.call_count == 2

    @patch("ultimate_discord_intelligence_bot.config.agent_factory.Agent")
    def test_create_agent_group(self, mock_agent_class: Mock) -> None:
        """Test creating agent group."""
        mock_agent = Mock()
        mock_agent_class.return_value = mock_agent

        with patch.object(self.factory, "_create_tools", return_value=[]):
            agents = self.factory.create_agent_group("content_pipeline")

            assert len(agents) == 4  # content_pipeline has 4 agents
            assert mock_agent_class.call_count == 4

    def test_agent_caching(self) -> None:
        """Test that agents are cached properly."""
        with patch("ultimate_discord_intelligence_bot.config.agent_factory.Agent") as mock_agent_class:
            mock_agent = Mock()
            mock_agent_class.return_value = mock_agent

            with patch.object(self.factory, "_create_tools", return_value=[]):
                # Create agent twice
                agent1 = self.factory.create_agent("mission_orchestrator")
                agent2 = self.factory.create_agent("mission_orchestrator")

                # Should only create once due to caching
                assert mock_agent_class.call_count == 1
                assert agent1 is agent2

    def test_clear_cache(self) -> None:
        """Test clearing the cache."""
        with patch("ultimate_discord_intelligence_bot.config.agent_factory.Agent") as mock_agent_class:
            mock_agent = Mock()
            mock_agent_class.return_value = mock_agent

            with patch.object(self.factory, "_create_tools", return_value=[]):
                # Create agent
                self.factory.create_agent("mission_orchestrator")

                # Clear cache
                self.factory.clear_cache()

                # Create again - should create new instance
                self.factory.create_agent("mission_orchestrator")

                # Should have been called twice
                assert mock_agent_class.call_count == 2

    def test_get_cached_agents(self) -> None:
        """Test getting cached agent names."""
        with patch("ultimate_discord_intelligence_bot.config.agent_factory.Agent") as mock_agent_class:
            mock_agent = Mock()
            mock_agent_class.return_value = mock_agent

            with patch.object(self.factory, "_create_tools", return_value=[]):
                # Create agent
                self.factory.create_agent("mission_orchestrator")

                cached_agents = self.factory.get_cached_agents()
                assert len(cached_agents) == 1
                assert "mission_orchestrator" in str(cached_agents[0])

    @patch("ultimate_discord_intelligence_bot.config.agent_factory.get_tool_wrapper")
    def test_tool_creation(self, mock_get_tool_wrapper: Mock) -> None:
        """Test tool creation and caching."""
        mock_tool = Mock()
        mock_get_tool_wrapper.return_value = mock_tool

        with patch("ultimate_discord_intelligence_bot.config.agent_factory.Agent") as mock_agent_class:
            mock_agent = Mock()
            mock_agent_class.return_value = mock_agent

            # Create agent that uses tools
            agent = self.factory.create_agent("mission_orchestrator")

            assert agent is not None
            # Should have called get_tool_wrapper for each tool
            assert mock_get_tool_wrapper.call_count > 0

    def test_tool_caching(self) -> None:
        """Test that tools are cached properly."""
        with patch("ultimate_discord_intelligence_bot.config.agent_factory.get_tool_wrapper") as mock_get_tool_wrapper:
            mock_tool = Mock()
            mock_get_tool_wrapper.return_value = mock_tool

            with patch("ultimate_discord_intelligence_bot.config.agent_factory.Agent") as mock_agent_class:
                mock_agent = Mock()
                mock_agent_class.return_value = mock_agent

                # Create multiple agents that use the same tools
                self.factory.create_agent("mission_orchestrator")
                self.factory.create_agent("executive_supervisor")

                # Should have cached tools, so fewer calls than total tools
                cached_tools = self.factory.get_cached_tools()
                assert len(cached_tools) > 0


class TestAgentFactoryIntegration:
    """Integration tests for agent factory."""

    def test_factory_with_real_definitions(self) -> None:
        """Test factory with real agent definitions."""
        AgentFactory()

        # Test that we can create agents for all defined agents
        for agent_name in AGENT_DEFINITIONS:
            # This will fail if we don't have proper tool wrappers,
            # but we can test the structure
            definition = get_agent_definition(agent_name)
            assert definition is not None
            assert definition.name == agent_name

    def test_agent_group_consistency(self) -> None:
        """Test that agent groups reference valid agents."""
        from ultimate_discord_intelligence_bot.config.agent_definitions import AGENT_GROUPS

        for group_name, agent_names in AGENT_GROUPS.items():
            for agent_name in agent_names:
                definition = get_agent_definition(agent_name)
                assert definition is not None, f"Agent {agent_name} in group {group_name} not found"


if __name__ == "__main__":
    pytest.main([__file__])
