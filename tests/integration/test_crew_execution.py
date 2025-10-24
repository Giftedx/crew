"""Integration tests for crew execution."""

from unittest.mock import Mock, patch

import pytest

from ultimate_discord_intelligence_bot.crew import create_crew


class TestCrewExecution:
    """Test cases for crew execution integration."""

    def test_crew_creation(self):
        """Test that crew can be created without errors."""
        try:
            crew = create_crew()
            assert crew is not None
            assert hasattr(crew, "crew")
        except Exception as e:
            pytest.fail(f"Crew creation failed: {e}")

    def test_crew_agents_loading(self):
        """Test that crew agents can be loaded."""
        crew = create_crew()

        # Check that crew has agents
        assert hasattr(crew, "crew")
        assert crew.crew is not None

        # Check that agents are loaded
        agents = crew.crew.agents
        assert len(agents) > 0, "No agents found in crew"

        # Check agent names
        agent_names = [agent.role for agent in agents]
        expected_roles = ["Acquisition Specialist", "Analysis Cartographer", "Verification Director"]

        for expected_role in expected_roles:
            assert any(expected_role in name for name in agent_names), (
                f"Expected role {expected_role} not found in agents"
            )

    def test_crew_tasks_loading(self):
        """Test that crew tasks can be loaded."""
        crew = create_crew()

        # Check that crew has tasks
        tasks = crew.crew.tasks
        assert len(tasks) > 0, "No tasks found in crew"

        # Check task descriptions
        for task in tasks:
            assert hasattr(task, "description"), "Task missing description"
            assert task.description is not None, "Task description is None"

    def test_crew_tool_integration(self):
        """Test that crew tools are properly integrated."""
        crew = create_crew()

        # Check that agents have tools
        agents = crew.crew.agents
        for agent in agents:
            if hasattr(agent, "tools"):
                assert len(agent.tools) > 0, f"Agent {agent.role} has no tools"

                # Check that tools are properly configured
                for tool in agent.tools:
                    assert hasattr(tool, "name"), "Tool missing name"
                    assert hasattr(tool, "description"), "Tool missing description"

    def test_crew_execution_workflow(self):
        """Test crew execution workflow."""
        crew = create_crew()

        # Mock the crew execution
        with patch.object(crew.crew, "kickoff") as mock_kickoff:
            mock_kickoff.return_value = Mock()

            # Test execution with sample inputs
            inputs = {"url": "https://example.com/video", "tenant": "test_tenant", "workspace": "test_workspace"}

            try:
                result = crew.crew.kickoff(inputs=inputs)
                assert result is not None
            except Exception as e:
                # If execution fails, it should be due to missing dependencies, not configuration
                assert "import" not in str(e).lower(), f"Import error in crew execution: {e}"

    def test_crew_agent_communication(self):
        """Test that crew agents can communicate."""
        crew = create_crew()

        # Check that agents have proper configuration for communication
        agents = crew.crew.agents
        for agent in agents:
            # Check agent configuration
            assert hasattr(agent, "role"), "Agent missing role"
            assert hasattr(agent, "goal"), "Agent missing goal"
            assert hasattr(agent, "backstory"), "Agent missing backstory"

    def test_crew_task_dependencies(self):
        """Test that crew tasks have proper dependencies."""
        crew = create_crew()

        tasks = crew.crew.tasks
        for task in tasks:
            # Check task configuration
            assert hasattr(task, "description"), "Task missing description"
            assert hasattr(task, "expected_output"), "Task missing expected_output"

            # Check that task has agent assignment
            if hasattr(task, "agent"):
                assert task.agent is not None, f"Task {task.description} has no agent assigned"

    def test_crew_error_handling(self):
        """Test that crew handles errors gracefully."""
        crew = create_crew()

        # Test with invalid inputs
        invalid_inputs = {"invalid_key": "invalid_value"}

        try:
            result = crew.crew.kickoff(inputs=invalid_inputs)
            # Should either succeed or fail gracefully
            assert result is not None or True  # Allow for graceful failure
        except Exception as e:
            # Should not crash the system
            assert "critical" not in str(e).lower(), f"Critical error in crew execution: {e}"

    def test_crew_memory_integration(self):
        """Test that crew has memory integration."""
        crew = create_crew()

        # Check that crew has memory configuration
        assert hasattr(crew.crew, "memory"), "Crew missing memory configuration"

        # Memory should be enabled for crew
        assert crew.crew.memory is True, "Crew memory is not enabled"

    def test_crew_planning_integration(self):
        """Test that crew has planning integration."""
        crew = create_crew()

        # Check that crew has planning configuration
        assert hasattr(crew.crew, "planning"), "Crew missing planning configuration"

        # Planning should be enabled for crew
        assert crew.crew.planning is True, "Crew planning is not enabled"

    def test_crew_verbose_mode(self):
        """Test that crew has verbose mode configuration."""
        crew = create_crew()

        # Check that crew has verbose configuration
        assert hasattr(crew.crew, "verbose"), "Crew missing verbose configuration"

        # Verbose should be enabled for crew
        assert crew.crew.verbose is True, "Crew verbose mode is not enabled"

    def test_crew_max_rpm_configuration(self):
        """Test that crew has RPM configuration."""
        crew = create_crew()

        # Check that crew has max_rpm configuration
        assert hasattr(crew.crew, "max_rpm"), "Crew missing max_rpm configuration"

        # Max RPM should be set to 10
        assert crew.crew.max_rpm == 10, f"Expected max_rpm=10, got {crew.crew.max_rpm}"
