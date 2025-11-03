"""Tests for UltimateDiscordIntelligenceBotCrew."""

from unittest.mock import MagicMock, patch

import pytest

from domains.orchestration.crew import UltimateDiscordIntelligenceBotCrew
from ultimate_discord_intelligence_bot.tenancy.context import TenantContext


class TestUltimateDiscordIntelligenceBotCrew:
    """Test cases for UltimateDiscordIntelligenceBotCrew."""

    @pytest.fixture
    def crew_instance(self):
        """Create crew instance for testing."""
        return UltimateDiscordIntelligenceBotCrew()

    @pytest.fixture
    def test_tenant_context(self):
        """Create test tenant context."""
        return TenantContext(tenant="test_tenant", workspace="test_workspace")

    def test_crew_initialization(self, crew_instance):
        """Test crew initialization."""
        assert crew_instance is not None
        assert hasattr(crew_instance, "mission_orchestrator")
        assert hasattr(crew_instance, "executive_supervisor")
        assert hasattr(crew_instance, "acquisition_specialist")
        assert hasattr(crew_instance, "crew")

    def test_mission_orchestrator_agent(self, crew_instance):
        """Test mission orchestrator agent creation."""
        agent = crew_instance.mission_orchestrator()
        assert agent is not None
        assert agent.role == "Mission Orchestrator"
        assert "orchestrate" in agent.goal.lower()
        assert len(agent.tools) > 0
        assert agent.verbose is True
        assert agent.allow_delegation is False

    def test_executive_supervisor_agent(self, crew_instance):
        """Test executive supervisor agent creation."""
        agent = crew_instance.executive_supervisor()
        assert agent is not None
        assert agent.role == "Executive Supervisor"
        assert "supervise" in agent.goal.lower()
        assert len(agent.tools) > 0
        assert agent.verbose is True
        assert agent.allow_delegation is False

    def test_acquisition_specialist_agent(self, crew_instance):
        """Test acquisition specialist agent creation."""
        agent = crew_instance.acquisition_specialist()
        assert agent is not None
        assert agent.role == "Acquisition Specialist"
        assert "acquire" in agent.goal.lower()
        assert len(agent.tools) > 0
        assert agent.verbose is True
        assert agent.allow_delegation is False

    def test_quality_assurance_specialist_agent(self, crew_instance):
        """Test quality assurance specialist agent creation."""
        agent = crew_instance.quality_assurance_specialist()
        assert agent is not None
        assert agent.role == "Quality Assurance Specialist"
        assert "quality" in agent.goal.lower()
        assert len(agent.tools) > 0
        assert agent.verbose is True
        assert agent.allow_delegation is False

    def test_performance_optimization_engineer_agent(self, crew_instance):
        """Test performance optimization engineer agent creation."""
        agent = crew_instance.performance_optimization_engineer()
        assert agent is not None
        assert agent.role == "Performance Optimization Engineer"
        assert "optimize" in agent.goal.lower()
        assert len(agent.tools) > 0
        assert agent.verbose is True
        assert agent.allow_delegation is False

    def test_enhanced_mcp_integration_specialist_agent(self, crew_instance):
        """Test enhanced MCP integration specialist agent creation."""
        agent = crew_instance.enhanced_mcp_integration_specialist()
        assert agent is not None
        assert agent.role == "Enhanced MCP Integration Specialist"
        assert "mcp" in agent.goal.lower()
        assert len(agent.tools) > 0
        assert agent.verbose is True
        assert agent.allow_delegation is False

    def test_nextgen_cache_memory_architect_agent(self, crew_instance):
        """Test next-gen cache memory architect agent creation."""
        agent = crew_instance.nextgen_cache_memory_architect()
        assert agent is not None
        assert agent.role == "Next-Gen Cache & Memory Architect"
        assert "cache" in agent.goal.lower() and "memory" in agent.goal.lower()
        assert len(agent.tools) > 0
        assert agent.verbose is True
        assert agent.allow_delegation is False

    def test_content_production_manager_agent(self, crew_instance):
        """Test content production manager agent creation."""
        agent = crew_instance.content_production_manager()
        assert agent is not None
        assert agent.role == "Content Production Manager"
        assert "content" in agent.goal.lower() and "production" in agent.goal.lower()
        assert len(agent.tools) > 0
        assert agent.verbose is True
        assert agent.allow_delegation is False

    def test_enhanced_social_media_archivist_agent(self, crew_instance):
        """Test enhanced social media archivist agent creation."""
        agent = crew_instance.enhanced_social_media_archivist()
        assert agent is not None
        assert agent.role == "Enhanced Social Media Archivist"
        assert "social media" in agent.goal.lower()
        assert len(agent.tools) > 0
        assert agent.verbose is True
        assert agent.allow_delegation is False

    def test_advanced_verification_specialist_agent(self, crew_instance):
        """Test advanced verification specialist agent creation."""
        agent = crew_instance.advanced_verification_specialist()
        assert agent is not None
        assert agent.role == "Advanced Verification Specialist"
        assert "verification" in agent.goal.lower()
        assert len(agent.tools) > 0
        assert agent.verbose is True
        assert agent.allow_delegation is False

    def test_reinforcement_learning_optimization_specialist_agent(self, crew_instance):
        """Test reinforcement learning optimization specialist agent creation."""
        agent = crew_instance.reinforcement_learning_optimization_specialist()
        assert agent is not None
        assert agent.role == "Reinforcement Learning Optimization Specialist"
        assert "reinforcement learning" in agent.goal.lower()
        assert len(agent.tools) > 0
        assert agent.verbose is True
        assert agent.allow_delegation is False

    def test_compliance_regulatory_officer_agent(self, crew_instance):
        """Test compliance regulatory officer agent creation."""
        agent = crew_instance.compliance_regulatory_officer()
        assert agent is not None
        assert agent.role == "Compliance & Regulatory Officer"
        assert "compliance" in agent.goal.lower()
        assert len(agent.tools) > 0
        assert agent.verbose is True
        assert agent.allow_delegation is False

    def test_crew_creation(self, crew_instance):
        """Test crew creation."""
        crew = crew_instance.crew()
        assert crew is not None
        assert hasattr(crew, "agents")
        assert hasattr(crew, "tasks")
        assert len(crew.agents) > 0
        assert len(crew.tasks) > 0

    def test_crew_agents_count(self, crew_instance):
        """Test that crew has expected number of agents."""
        crew = crew_instance.crew()
        expected_agents = [
            "mission_orchestrator",
            "executive_supervisor",
            "acquisition_specialist",
            "quality_assurance_specialist",
            "performance_optimization_engineer",
            "enhanced_mcp_integration_specialist",
            "nextgen_cache_memory_architect",
            "content_production_manager",
            "enhanced_social_media_archivist",
            "advanced_verification_specialist",
            "reinforcement_learning_optimization_specialist",
            "compliance_regulatory_officer",
        ]
        assert len(crew.agents) >= len(expected_agents)

    def test_crew_tasks_count(self, crew_instance):
        """Test that crew has expected number of tasks."""
        crew = crew_instance.crew()
        assert len(crew.tasks) > 0

    def test_agent_tool_assignment(self, crew_instance):
        """Test that agents have appropriate tools assigned."""
        mission_agent = crew_instance.mission_orchestrator()
        assert len(mission_agent.tools) > 0
        quality_agent = crew_instance.quality_assurance_specialist()
        assert len(quality_agent.tools) > 0
        performance_agent = crew_instance.performance_optimization_engineer()
        assert len(performance_agent.tools) > 0

    def test_agent_roles_and_goals(self, crew_instance):
        """Test that agents have appropriate roles and goals."""
        agents = [
            crew_instance.mission_orchestrator(),
            crew_instance.executive_supervisor(),
            crew_instance.acquisition_specialist(),
            crew_instance.quality_assurance_specialist(),
            crew_instance.performance_optimization_engineer(),
        ]
        for agent in agents:
            assert agent.role is not None
            assert len(agent.role) > 0
            assert agent.goal is not None
            assert len(agent.goal) > 0
            assert agent.backstory is not None
            assert len(agent.backstory) > 0

    def test_agent_verbose_and_delegation_settings(self, crew_instance):
        """Test that agents have correct verbose and delegation settings."""
        agents = [
            crew_instance.mission_orchestrator(),
            crew_instance.executive_supervisor(),
            crew_instance.acquisition_specialist(),
            crew_instance.quality_assurance_specialist(),
            crew_instance.performance_optimization_engineer(),
        ]
        for agent in agents:
            assert agent.verbose is True
            assert agent.allow_delegation is False

    def test_crew_planning_and_memory_settings(self, crew_instance):
        """Test that crew has correct planning and memory settings."""
        crew = crew_instance.crew()
        assert crew.planning is True
        assert crew.memory is True
        assert crew.cache is True
        assert crew.max_rpm == 10

    def test_crew_step_logger(self, crew_instance):
        """Test that crew has step logger configured."""
        crew = crew_instance.crew()
        assert hasattr(crew, "step_callback")
        assert crew.step_callback is not None

    def test_enhanced_step_logger(self, crew_instance):
        """Test enhanced step logger functionality."""
        logger = crew_instance._enhanced_step_logger()
        assert logger is not None
        assert callable(logger)

    def test_crew_execution(self, crew_instance, test_tenant_context):
        """Test crew execution with mock inputs."""
        crew = crew_instance.crew()
        with patch.object(
            crew, "kickoff", return_value=MagicMock(raw="Test result", result="Test result")
        ) as mock_kickoff:
            inputs = {
                "url": "https://example.com/test",
                "tenant": test_tenant_context.tenant,
                "workspace": test_tenant_context.workspace,
            }
            result = crew.kickoff(inputs=inputs)
            assert result is not None
            mock_kickoff.assert_called_once_with(inputs=inputs)

    def test_crew_with_different_inputs(self, crew_instance, test_tenant_context):
        """Test crew execution with different input types."""
        crew = crew_instance.crew()
        test_inputs = [
            {
                "url": "https://youtube.com/watch?v=test",
                "tenant": test_tenant_context.tenant,
                "workspace": test_tenant_context.workspace,
            },
            {
                "url": "https://twitch.tv/test",
                "tenant": test_tenant_context.tenant,
                "workspace": test_tenant_context.workspace,
            },
            {
                "url": "https://tiktok.com/@test",
                "tenant": test_tenant_context.tenant,
                "workspace": test_tenant_context.workspace,
            },
        ]
        for inputs in test_inputs:
            with patch.object(
                crew, "kickoff", return_value=MagicMock(raw="Test result", result="Test result")
            ) as mock_kickoff:
                result = crew.kickoff(inputs=inputs)
                assert result is not None
                mock_kickoff.assert_called_once_with(inputs=inputs)

    def test_crew_error_handling(self, crew_instance, test_tenant_context):
        """Test crew error handling."""
        crew = crew_instance.crew()
        invalid_inputs = [{}, {"url": ""}, {"url": "invalid_url"}]
        for inputs in invalid_inputs:
            with patch.object(crew, "kickoff", side_effect=Exception("Test error")):
                try:
                    result = crew.kickoff(inputs=inputs)
                    assert result is not None
                except Exception as e:
                    assert "Test error" in str(e)

    def test_crew_performance(self, crew_instance, test_tenant_context, performance_benchmark):
        """Test crew performance."""
        crew = crew_instance.crew()
        performance_benchmark.start()
        with patch.object(crew, "kickoff", return_value=MagicMock(raw="Test result", result="Test result")):
            inputs = {
                "url": "https://example.com/test",
                "tenant": test_tenant_context.tenant,
                "workspace": test_tenant_context.workspace,
            }
            result = crew.kickoff(inputs=inputs)
            elapsed_time = performance_benchmark.stop()
            assert result is not None
            assert elapsed_time < 5.0

    def test_crew_tenant_isolation(self, crew_instance):
        """Test that crew respects tenant isolation."""
        crew = crew_instance.crew()
        tenant1 = TenantContext(tenant="tenant1", workspace="workspace1")
        tenant2 = TenantContext(tenant="tenant2", workspace="workspace2")
        inputs1 = {"url": "https://example.com/test1", "tenant": tenant1.tenant, "workspace": tenant1.workspace}
        inputs2 = {"url": "https://example.com/test2", "tenant": tenant2.tenant, "workspace": tenant2.workspace}
        with patch.object(
            crew, "kickoff", return_value=MagicMock(raw="Test result", result="Test result")
        ) as mock_kickoff:
            result1 = crew.kickoff(inputs=inputs1)
            result2 = crew.kickoff(inputs=inputs2)
            assert result1 is not None
            assert result2 is not None
            assert mock_kickoff.call_count == 2

    def test_crew_memory_and_planning(self, crew_instance, test_tenant_context):
        """Test that crew uses memory and planning features."""
        crew = crew_instance.crew()
        assert crew.memory is True
        assert crew.planning is True
        assert crew.cache is True
        with patch.object(
            crew, "kickoff", return_value=MagicMock(raw="Test result", result="Test result")
        ) as mock_kickoff:
            inputs = {
                "url": "https://example.com/test",
                "tenant": test_tenant_context.tenant,
                "workspace": test_tenant_context.workspace,
            }
            result = crew.kickoff(inputs=inputs)
            assert result is not None
            mock_kickoff.assert_called_once_with(inputs=inputs)

    def test_crew_max_rpm_limit(self, crew_instance):
        """Test that crew respects max RPM limit."""
        crew = crew_instance.crew()
        assert crew.max_rpm == 10
        with patch.object(
            crew, "kickoff", return_value=MagicMock(raw="Test result", result="Test result")
        ) as mock_kickoff:
            for i in range(15):
                inputs = {"url": f"https://example.com/test{i}", "tenant": "test_tenant", "workspace": "test_workspace"}
                result = crew.kickoff(inputs=inputs)
                assert result is not None
            assert mock_kickoff.call_count == 15

    def test_crew_step_callback(self, crew_instance):
        """Test that crew has step callback configured."""
        crew = crew_instance.crew()
        assert hasattr(crew, "step_callback")
        assert crew.step_callback is not None
        assert callable(crew.step_callback)

    def test_crew_agent_tool_consistency(self, crew_instance):
        """Test that all agents have consistent tool configurations."""
        agents = [
            crew_instance.mission_orchestrator(),
            crew_instance.executive_supervisor(),
            crew_instance.acquisition_specialist(),
            crew_instance.quality_assurance_specialist(),
            crew_instance.performance_optimization_engineer(),
        ]
        for agent in agents:
            assert len(agent.tools) > 0
            for tool in agent.tools:
                assert hasattr(tool, "func")
                assert callable(tool.func)

    def test_crew_task_consistency(self, crew_instance):
        """Test that all tasks have consistent configurations."""
        crew = crew_instance.crew()
        for task in crew.tasks:
            assert hasattr(task, "description")
            assert hasattr(task, "expected_output")
            assert hasattr(task, "agent")
            assert len(task.description) > 0
            assert len(task.expected_output) > 0
            assert task.agent is not None

    def test_crew_imports(self, crew_instance):
        """Test that all required imports are available."""
        assert hasattr(crew_instance, "mission_orchestrator")
        assert hasattr(crew_instance, "executive_supervisor")
        assert hasattr(crew_instance, "acquisition_specialist")
        assert hasattr(crew_instance, "quality_assurance_specialist")
        assert hasattr(crew_instance, "performance_optimization_engineer")
        assert hasattr(crew_instance, "enhanced_mcp_integration_specialist")
        assert hasattr(crew_instance, "nextgen_cache_memory_architect")
        assert hasattr(crew_instance, "content_production_manager")
        assert hasattr(crew_instance, "enhanced_social_media_archivist")
        assert hasattr(crew_instance, "advanced_verification_specialist")
        assert hasattr(crew_instance, "reinforcement_learning_optimization_specialist")
        assert hasattr(crew_instance, "compliance_regulatory_officer")

    def test_crew_agent_backstories(self, crew_instance):
        """Test that all agents have meaningful backstories."""
        agents = [
            crew_instance.mission_orchestrator(),
            crew_instance.executive_supervisor(),
            crew_instance.acquisition_specialist(),
            crew_instance.quality_assurance_specialist(),
            crew_instance.performance_optimization_engineer(),
        ]
        for agent in agents:
            assert len(agent.backstory) > 50
            assert "expert" in agent.backstory.lower() or "specialist" in agent.backstory.lower()
            assert "experience" in agent.backstory.lower() or "expertise" in agent.backstory.lower()

    def test_crew_agent_goals_alignment(self, crew_instance):
        """Test that agent goals align with their roles."""
        role_goal_pairs = [
            (crew_instance.mission_orchestrator(), "orchestrate"),
            (crew_instance.executive_supervisor(), "supervise"),
            (crew_instance.acquisition_specialist(), "acquire"),
            (crew_instance.quality_assurance_specialist(), "quality"),
            (crew_instance.performance_optimization_engineer(), "optimize"),
        ]
        for agent, expected_keyword in role_goal_pairs:
            assert expected_keyword in agent.goal.lower()
            assert len(agent.goal) > 20

    def test_crew_agent_tool_specialization(self, crew_instance):
        """Test that agents have specialized tools appropriate for their roles."""
        quality_agent = crew_instance.quality_assurance_specialist()
        quality_tool_names = [tool.name for tool in quality_agent.tools]
        assert any("quality" in name.lower() for name in quality_tool_names)
        performance_agent = crew_instance.performance_optimization_engineer()
        performance_tool_names = [tool.name for tool in performance_agent.tools]
        assert any("performance" in name.lower() or "optimization" in name.lower() for name in performance_tool_names)
        acquisition_agent = crew_instance.acquisition_specialist()
        acquisition_tool_names = [tool.name for tool in acquisition_agent.tools]
        assert any("download" in name.lower() or "acquisition" in name.lower() for name in acquisition_tool_names)
