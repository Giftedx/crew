"""Tests for the BaseAgent class."""
import pytest
from domains.orchestration.agents.base import BaseAgent
from ultimate_discord_intelligence_bot.tools._base import BaseTool

class MockTestAgent(BaseAgent):
    """Test agent implementation."""

    @property
    def role(self) -> str:
        return 'Test Agent'

    @property
    def goal(self) -> str:
        return 'Test goal'

    @property
    def backstory(self) -> str:
        return 'Test backstory'

class TestTool(BaseTool):
    """Test tool implementation."""

    def _run(self, *args, **kwargs):
        return {'result': 'test'}

class TestBaseAgent:
    """Test suite for BaseAgent class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.agent = MockTestAgent()
        self.tool = TestTool()

    def test_agent_creation(self):
        """Test agent can be created."""
        assert self.agent.role == 'Test Agent'
        assert self.agent.goal == 'Test goal'
        assert self.agent.backstory == 'Test backstory'
        assert self.agent.verbose is True
        assert self.agent.allow_delegation is False

    def test_add_tool(self):
        """Test adding tools to agent."""
        initial_count = len(self.agent._tools)
        self.agent.add_tool(self.tool)
        assert len(self.agent._tools) == initial_count + 1
        assert self.tool in self.agent._tools

    def test_create_agent(self):
        """Test creating CrewAI Agent instance."""
        self.agent.add_tool(self.tool)
        try:
            result = self.agent.create()
            assert result is not None
        except ImportError:
            pytest.skip('crewai not available for testing')

    def test_agent_with_tools(self):
        """Test agent initialization with tools."""
        tools = [TestTool(), TestTool()]
        agent = MockTestAgent(tools=tools)
        assert len(agent._tools) == 2
        assert all((isinstance(tool, TestTool) for tool in agent._tools))