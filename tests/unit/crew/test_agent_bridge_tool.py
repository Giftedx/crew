"""Tests for AgentBridgeTool."""

from platform.core.step_result import StepResult
from unittest.mock import Mock, patch

from ultimate_discord_intelligence_bot.tools.agent_bridge_tool import AgentBridgeTool


class TestAgentBridgeTool:
    """Test suite for AgentBridgeTool."""

    def setup_method(self):
        """Set up test fixtures."""
        self.tool = AgentBridgeTool()

    def test_tool_initialization(self):
        """Test tool initializes correctly."""
        assert self.tool.name == "agent_bridge_tool"
        assert "agent communication" in self.tool.description

    def test_run_with_valid_agent_id(self):
        """Test tool with valid agent ID."""
        result = self.tool._run("test_agent", "test_message")
        assert isinstance(result, StepResult)

    def test_run_with_missing_agent_id(self):
        """Test tool with missing agent ID."""
        result = self.tool._run("", "test_message")
        assert not result.success
        assert "agent_id is required" in result.error

    def test_run_with_missing_message(self):
        """Test tool with missing message."""
        result = self.tool._run("test_agent", "")
        assert not result.success
        assert "message is required" in result.error

    def test_run_with_invalid_agent(self):
        """Test tool with invalid agent ID."""
        result = self.tool._run("invalid_agent", "test_message")
        assert isinstance(result, StepResult)

    def test_bridge_communication(self):
        """Test bridge communication functionality."""
        with patch("ultimate_discord_intelligence_bot.tools.agent_bridge_tool.get_agent_registry") as mock_registry:
            mock_agent = Mock()
            mock_agent.process_message.return_value = "response"
            mock_registry.return_value.get_agent.return_value = mock_agent
            result = self.tool._run("test_agent", "test_message")
            assert result.success
            assert "response" in result.data.get("response", "")
