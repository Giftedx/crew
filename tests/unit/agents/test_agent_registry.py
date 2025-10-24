"""Tests for the agent registry system."""

from ultimate_discord_intelligence_bot.agents.registry import AGENT_REGISTRY, get_agent, register_agent


class TestAgentRegistry:
    """Test suite for agent registry functionality."""

    def test_registry_initialization(self):
        """Test registry is properly initialized."""
        assert isinstance(AGENT_REGISTRY, dict)

    def test_register_agent_decorator(self):
        """Test agent registration decorator."""

        # Test decorator functionality
        @register_agent("test_agent")
        class TestAgent:
            pass

        # Check agent is registered
        assert "test_agent" in AGENT_REGISTRY
        assert AGENT_REGISTRY["test_agent"] == TestAgent

    def test_get_agent(self):
        """Test getting agent from registry."""

        # Register a test agent
        @register_agent("test_get_agent")
        class TestGetAgent:
            pass

        # Test getting the agent
        agent_class = get_agent("test_get_agent")
        assert agent_class == TestGetAgent

        # Test getting non-existent agent
        non_existent = get_agent("non_existent_agent")
        assert non_existent is None

    def test_agent_registration_flow(self):
        """Test complete agent registration flow."""
        # Clear registry for clean test
        original_registry = AGENT_REGISTRY.copy()
        AGENT_REGISTRY.clear()

        try:
            # Register multiple agents
            @register_agent("agent1")
            class Agent1:
                pass

            @register_agent("agent2")
            class Agent2:
                pass

            # Test registry contains agents
            assert len(AGENT_REGISTRY) == 2
            assert "agent1" in AGENT_REGISTRY
            assert "agent2" in AGENT_REGISTRY
            assert AGENT_REGISTRY["agent1"] == Agent1
            assert AGENT_REGISTRY["agent2"] == Agent2

            # Test getting agents
            assert get_agent("agent1") == Agent1
            assert get_agent("agent2") == Agent2

        finally:
            # Restore original registry
            AGENT_REGISTRY.clear()
            AGENT_REGISTRY.update(original_registry)
