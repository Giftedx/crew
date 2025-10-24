"""Integration tests for content analysis workflows."""

from unittest.mock import Mock, patch

from ultimate_discord_intelligence_bot.crew import UltimateDiscordIntelligenceBotCrew


class TestContentAnalysisWorkflow:
    """Test suite for content analysis integration workflows."""

    def setup_method(self):
        """Set up test fixtures."""
        self.crew = UltimateDiscordIntelligenceBotCrew()

    def test_crew_instantiation(self):
        """Test crew can be instantiated."""
        assert self.crew is not None
        assert hasattr(self.crew, "_execution_trace")
        assert hasattr(self.crew, "_execution_start_time")
        assert hasattr(self.crew, "_current_step_count")

    def test_crew_has_agents(self):
        """Test crew has all required agents."""
        crew_obj = self.crew.crew()
        assert hasattr(crew_obj, "agents")
        assert len(crew_obj.agents) > 0

    def test_crew_has_tasks(self):
        """Test crew has all required tasks."""
        crew_obj = self.crew.crew()
        assert hasattr(crew_obj, "tasks")
        assert len(crew_obj.tasks) > 0

    @patch("crewai.Crew")
    def test_crew_construction(self, mock_crew_class):
        """Test crew construction with proper configuration."""
        mock_crew = Mock()
        mock_crew_class.return_value = mock_crew

        crew_obj = self.crew.crew()

        mock_crew_class.assert_called_once()
        call_args = mock_crew_class.call_args
        assert call_args[1]["process"] == "sequential"
        assert call_args[1]["verbose"] is True
        assert call_args[1]["planning"] is True
        assert call_args[1]["memory"] is True
        assert call_args[1]["cache"] is True
        assert call_args[1]["max_rpm"] == 10

    def test_agent_registry_integration(self):
        """Test agent registry integration."""
        from ultimate_discord_intelligence_bot.agents.registry import get_agent

        # Test that all agents are registered
        agent_names = [
            "mission_orchestrator",
            "acquisition_specialist",
            "transcription_engineer",
            "analysis_cartographer",
            "verification_director",
            "knowledge_integrator",
            "system_reliability_officer",
            "community_liaison",
        ]

        for name in agent_names:
            agent_class = get_agent(name)
            assert agent_class is not None, f"Agent {name} not found in registry"

    def test_execution_trace_initialization(self):
        """Test execution trace is properly initialized."""
        assert self.crew._execution_trace == []
        assert self.crew._execution_start_time is None
        assert self.crew._current_step_count == 0

    def test_enhanced_step_logger(self):
        """Test enhanced step logger functionality."""
        # Create a mock step
        mock_step = Mock()
        mock_step.agent = Mock()
        mock_step.agent.role = "Test Agent"
        mock_step.tool = "Test Tool"
        mock_step.raw = "Test output"
        mock_step.step_type = "test"
        mock_step.status = "success"

        # Test step logging
        self.crew._enhanced_step_logger(mock_step)

        assert self.crew._current_step_count == 1
        assert len(self.crew._execution_trace) == 1
        assert self.crew._execution_trace[0]["agent_role"] == "Test Agent"
        assert self.crew._execution_trace[0]["tool"] == "Test Tool"

    def test_execution_summary(self):
        """Test execution summary generation."""
        # Add some mock trace data
        self.crew._execution_trace = [{"agent_role": "Test Agent", "tool": "Test Tool", "step_type": "test"}]
        self.crew._current_step_count = 1
        self.crew._execution_start_time = 0.0

        summary = self.crew.get_execution_summary()

        assert summary["total_steps"] == 1
        assert "Test Agent" in summary["agents_involved"]
        assert "Test Tool" in summary["tools_used"]
        assert len(summary["recent_steps"]) == 1
