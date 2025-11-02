"""Tests for the agent registry system."""

from domains.orchestration.agents.registry import AGENT_REGISTRY, get_agent, register_agent


class TestAgentRegistry:
    """Test suite for agent registry functionality."""

    def test_registry_initialization(self):
        """Test registry is properly initialized."""
        assert isinstance(AGENT_REGISTRY, dict)

    def test_register_agent_decorator(self):
        """Test agent registration decorator."""

        @register_agent("test_agent")
        class TestAgent:
            pass

        assert "test_agent" in AGENT_REGISTRY
        assert AGENT_REGISTRY["test_agent"] == TestAgent

    def test_get_agent(self):
        """Test getting agent from registry."""

        @register_agent("test_get_agent")
        class TestGetAgent:
            pass

        agent_class = get_agent("test_get_agent")
        assert agent_class == TestGetAgent
        non_existent = get_agent("non_existent_agent")
        assert non_existent is None

    def test_agent_registration_flow(self):
        """Test complete agent registration flow."""
        original_registry = AGENT_REGISTRY.copy()
        AGENT_REGISTRY.clear()
        try:

            @register_agent("agent1")
            class Agent1:
                pass

            @register_agent("agent2")
            class Agent2:
                pass

            assert len(AGENT_REGISTRY) == 2
            assert "agent1" in AGENT_REGISTRY
            assert "agent2" in AGENT_REGISTRY
            assert AGENT_REGISTRY["agent1"] == Agent1
            assert AGENT_REGISTRY["agent2"] == Agent2
            assert get_agent("agent1") == Agent1
            assert get_agent("agent2") == Agent2
        finally:
            AGENT_REGISTRY.clear()
            AGENT_REGISTRY.update(original_registry)
