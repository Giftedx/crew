"""Tests for the Acquisition Specialist Agent."""

from unittest.mock import Mock, patch

from domains.orchestration.agents.acquisition.acquisition_specialist import AcquisitionSpecialistAgent


class TestAcquisitionSpecialistAgent:
    """Test suite for Acquisition Specialist Agent."""

    def setup_method(self):
        """Set up test fixtures."""
        self.agent = AcquisitionSpecialistAgent()

    def test_agent_properties(self):
        """Test agent properties."""
        assert self.agent.role == "Acquisition Specialist"
        assert "Capture pristine source media" in self.agent.goal
        assert "Multi-platform capture expert" in self.agent.backstory
        assert self.agent.allow_delegation is False

    def test_agent_has_tools(self):
        """Test agent has required tools."""
        assert len(self.agent._tools) > 0
        tool_names = [tool.__class__.__name__ for tool in self.agent._tools]
        assert "MultiPlatformDownloadTool" in tool_names
        assert "YouTubeDownloadTool" in tool_names
        assert "TwitchDownloadTool" in tool_names

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
            assert call_args[1]["role"] == "Acquisition Specialist"
            assert call_args[1]["allow_delegation"] is False
            assert result == mock_agent

    def test_agent_registration(self):
        """Test agent is properly registered."""
        from domains.orchestration.agents.registry import get_agent

        agent_class = get_agent("acquisition_specialist")
        assert agent_class is not None
        assert agent_class == AcquisitionSpecialistAgent
