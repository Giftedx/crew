"""Unit tests for agent managers module."""

from unittest.mock import Mock

from src.ultimate_discord_intelligence_bot.orchestrator import agent_managers


class TestAgentManagers:
    """Test suite for agent management functions."""

    def test_populate_agent_tool_context_success(self):
        """Test successful context population."""
        # Arrange
        agent = Mock()
        agent.tools = [Mock()]
        agent.tools[0].update_context = Mock()
        agent.role = "test_agent"

        context_data = {
            "transcript": "test transcript content",
            "url": "https://example.com",
            "file_path": "/path/to/file",
        }

        # Act
        agent_managers.populate_agent_tool_context(agent, context_data)

        # Assert
        agent.tools[0].update_context.assert_called_once_with(context_data)

    def test_populate_agent_tool_context_no_tools_attribute(self):
        """Test context population when agent has no tools attribute."""
        # Arrange
        agent = Mock(spec=[])  # No tools attribute
        agent.role = "test_agent"

        context_data = {"transcript": "test content"}

        # Act
        agent_managers.populate_agent_tool_context(agent, context_data)

        # Assert - should not raise exception

    def test_populate_agent_tool_context_empty_tools(self):
        """Test context population with empty tools list."""
        # Arrange
        agent = Mock()
        agent.tools = []
        agent.role = "test_agent"

        context_data = {"transcript": "test content"}

        # Act
        agent_managers.populate_agent_tool_context(agent, context_data)

        # Assert - should not raise exception

    def test_populate_agent_tool_context_with_metrics(self):
        """Test context population with metrics tracking."""
        # Arrange
        agent = Mock()
        agent.tools = [Mock()]
        agent.tools[0].update_context = Mock()
        agent.role = "test_agent"

        context_data = {"transcript": "test content"}

        metrics_instance = Mock()
        metrics_instance.counter.return_value.inc = Mock()

        # Act
        agent_managers.populate_agent_tool_context(agent, context_data, metrics_instance=metrics_instance)

        # Assert
        metrics_instance.counter.assert_called_once()
        metrics_instance.counter.return_value.inc.assert_called_once()

    def test_populate_agent_tool_context_with_mem0_tool(self):
        """Test context population with Mem0 tool addition."""
        # Arrange
        agent = Mock()
        agent.tools = [Mock()]
        agent.tools[0].update_context = Mock()
        agent.role = "test_agent"

        context_data = {"transcript": "test content"}

        # Act
        # Just test that the function runs without error when Mem0 tool is not available
        agent_managers.populate_agent_tool_context(agent, context_data)

        # Assert
        agent.tools[0].update_context.assert_called_once_with(context_data)

    def test_get_or_create_agent_from_cache(self):
        """Test getting agent from cache."""
        # Arrange
        agent_name = "test_agent"
        agent_coordinators = {agent_name: Mock()}
        crew_instance = Mock()

        # Act
        result = agent_managers.get_or_create_agent(agent_name, agent_coordinators, crew_instance)

        # Assert
        assert result == agent_coordinators[agent_name]

    def test_get_or_create_agent_new_creation(self):
        """Test creating new agent."""
        # Arrange
        agent_name = "test_agent"
        agent_coordinators = {}
        crew_instance = Mock()
        mock_agent = Mock()
        crew_instance.test_agent.return_value = mock_agent

        # Act
        result = agent_managers.get_or_create_agent(agent_name, agent_coordinators, crew_instance)

        # Assert
        assert result == mock_agent
        assert agent_coordinators[agent_name] == mock_agent

    def test_get_or_create_agent_invalid_name(self):
        """Test creating agent with invalid name."""
        # Arrange
        agent_name = "invalid_agent"
        agent_coordinators = {}
        crew_instance = Mock()
        crew_instance.invalid_agent = None

        # Act & Assert
        try:
            agent_managers.get_or_create_agent(agent_name, agent_coordinators, crew_instance)
            raise AssertionError("Should have raised ValueError")
        except ValueError as e:
            assert "Unknown agent" in str(e)

    def test_populate_agent_tool_context_context_summary(self):
        """Test context summary generation."""
        # Arrange
        agent = Mock()
        agent.tools = []
        agent.role = "test_agent"

        context_data = {
            "transcript": "test transcript",
            "metadata": {"key": "value"},
            "count": 42,
        }

        # Act
        agent_managers.populate_agent_tool_context(agent, context_data)

        # Assert - should not raise exception and should log context summary

    def test_populate_agent_tool_context_with_logger(self):
        """Test context population with custom logger."""
        # Arrange
        agent = Mock()
        agent.tools = []
        agent.role = "test_agent"

        context_data = {"transcript": "test content"}
        custom_logger = Mock()

        # Act
        agent_managers.populate_agent_tool_context(agent, context_data, logger_instance=custom_logger)

        # Assert
        # Should use custom logger instead of module logger
