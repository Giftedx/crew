"""Tests for the Mission Orchestrator Agent."""

from unittest.mock import Mock, patch

from ultimate_discord_intelligence_bot.agents.operations.mission_orchestrator import MissionOrchestratorAgent


class TestMissionOrchestratorAgent:
    """Test suite for Mission Orchestrator Agent."""

    def setup_method(self):
        """Set up test fixtures."""
        self.agent = MissionOrchestratorAgent()

    def test_agent_properties(self):
        """Test agent properties."""
        assert self.agent.role == "Autonomy Mission Orchestrator"
        assert "Coordinate end-to-end missions" in self.agent.goal
        assert "Mission orchestration" in self.agent.backstory
        assert self.agent.allow_delegation is True

    def test_agent_has_tools(self):
        """Test agent has required tools."""
        assert len(self.agent._tools) > 0
        # Check for core tools
        tool_names = [tool.__class__.__name__ for tool in self.agent._tools]
        assert "PipelineTool" in tool_names
        assert "AdvancedPerformanceAnalyticsTool" in tool_names
        assert "TimelineTool" in tool_names

    @patch("ultimate_discord_intelligence_bot.crewai_tool_wrappers.wrap_tool_for_crewai")
    def test_create_agent(self, mock_wrap):
        """Test creating CrewAI Agent instance."""
        mock_wrap.return_value = "wrapped_tool"

        with patch("crewai.Agent") as mock_agent_class:
            mock_agent = Mock()
            mock_agent_class.return_value = mock_agent

            result = self.agent.create()

            mock_agent_class.assert_called_once()
            call_args = mock_agent_class.call_args
            assert call_args[1]["role"] == "Autonomy Mission Orchestrator"
            assert call_args[1]["allow_delegation"] is True
            assert result == mock_agent

    def test_agent_registration(self):
        """Test agent is properly registered."""
        from ultimate_discord_intelligence_bot.agents.registry import get_agent

        agent_class = get_agent("mission_orchestrator")
        assert agent_class is not None
        assert agent_class == MissionOrchestratorAgent
