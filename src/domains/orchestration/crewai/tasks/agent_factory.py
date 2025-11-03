"""Agent factory for creating agents from structured definitions.

This module provides a factory pattern for creating CrewAI agents from
structured definitions, making it easier to test and maintain agent configurations.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from app.config.agent_definitions import AgentDefinition, get_agent_definition
from ultimate_discord_intelligence_bot.crewai_tool_wrappers import get_tool_wrapper


if TYPE_CHECKING:
    from crewai import Agent
else:
    try:
        from crewai import Agent
    except ImportError:
        Agent = Any


class AgentFactory:
    """Factory for creating CrewAI agents from structured definitions."""

    def __init__(self) -> None:
        self.tool_cache: dict[str, Any] = {}
        self.agent_cache: dict[str, Agent] = {}

    def create_agent(self, agent_name: str, **overrides: Any) -> Agent | None:
        """Create an agent from its definition.

        Args:
            agent_name: Name of the agent to create
            **overrides: Override any agent definition parameters

        Returns:
            Created Agent instance or None if agent not found
        """
        definition = get_agent_definition(agent_name)
        if not definition:
            return None
        if overrides:
            definition = self._apply_overrides(definition, overrides)
        cache_key = f"{agent_name}:{hash(str(overrides))}"
        if cache_key in self.agent_cache:
            return self.agent_cache[cache_key]
        try:
            tools = self._create_tools(definition.tools)
            agent = Agent(
                role=definition.role,
                goal=definition.goal,
                backstory=definition.backstory,
                tools=tools,
                verbose=definition.verbose,
                allow_delegation=definition.allow_delegation,
                max_iter=definition.max_iter,
                memory=definition.memory,
                max_rpm=definition.max_rpm,
                max_execution_time=definition.max_execution_time,
                step_callback=self._get_step_callback(definition.step_callback),
                planning=definition.planning,
                max_retry_limit=definition.max_retry_limit,
                max_prompt_tokens=definition.max_prompt_tokens,
                max_completion_tokens=definition.max_completion_tokens,
                temperature=definition.temperature,
                top_p=definition.top_p,
            )
            self.agent_cache[cache_key] = agent
            return agent
        except Exception as e:
            print(f"Error creating agent {agent_name}: {e}")
            return None

    def create_agents(self, agent_names: list[str], **overrides: Any) -> list[Agent]:
        """Create multiple agents from their definitions.

        Args:
            agent_names: List of agent names to create
            **overrides: Override parameters for all agents

        Returns:
            List of created Agent instances
        """
        agents = []
        for name in agent_names:
            agent = self.create_agent(name, **overrides)
            if agent:
                agents.append(agent)
        return agents

    def create_agent_group(self, group_name: str, **overrides: Any) -> list[Agent]:
        """Create all agents in a group.

        Args:
            group_name: Name of the agent group
            **overrides: Override parameters for all agents

        Returns:
            List of created Agent instances
        """
        from app.config.agent_definitions import get_agent_group

        agent_names = get_agent_group(group_name)
        return self.create_agents(agent_names, **overrides)

    def _apply_overrides(self, definition: AgentDefinition, overrides: dict[str, Any]) -> AgentDefinition:
        """Apply overrides to an agent definition."""
        new_definition = AgentDefinition(
            name=definition.name,
            role=overrides.get("role", definition.role),
            goal=overrides.get("goal", definition.goal),
            backstory=overrides.get("backstory", definition.backstory),
            tools=overrides.get("tools", definition.tools),
            verbose=overrides.get("verbose", definition.verbose),
            allow_delegation=overrides.get("allow_delegation", definition.allow_delegation),
            max_iter=overrides.get("max_iter", definition.max_iter),
            memory=overrides.get("memory", definition.memory),
            max_rpm=overrides.get("max_rpm", definition.max_rpm),
            max_execution_time=overrides.get("max_execution_time", definition.max_execution_time),
            step_callback=overrides.get("step_callback", definition.step_callback),
            planning=overrides.get("planning", definition.planning),
            max_retry_limit=overrides.get("max_retry_limit", definition.max_retry_limit),
            max_prompt_tokens=overrides.get("max_prompt_tokens", definition.max_prompt_tokens),
            max_completion_tokens=overrides.get("max_completion_tokens", definition.max_completion_tokens),
            temperature=overrides.get("temperature", definition.temperature),
            top_p=overrides.get("top_p", definition.top_p),
            metadata=overrides.get("metadata", definition.metadata),
        )
        return new_definition

    def _create_tools(self, tool_names: list[str]) -> list[Any]:
        """Create tools from their names."""
        tools = []
        for tool_name in tool_names:
            tool = self._get_tool(tool_name)
            if tool:
                tools.append(tool)
        return tools

    def _get_tool(self, tool_name: str) -> Any | None:
        """Get a tool by name, using cache when possible."""
        if tool_name in self.tool_cache:
            return self.tool_cache[tool_name]
        try:
            tool = get_tool_wrapper(tool_name)
            if tool:
                self.tool_cache[tool_name] = tool
            return tool
        except Exception as e:
            print(f"Error creating tool {tool_name}: {e}")
            return None

    def _get_step_callback(self, callback_name: str | None) -> Any | None:
        """Get step callback function by name."""
        if not callback_name:
            return None
        return None

    def clear_cache(self) -> None:
        """Clear the agent and tool caches."""
        self.tool_cache.clear()
        self.agent_cache.clear()

    def get_cached_agents(self) -> list[str]:
        """Get list of cached agent names."""
        return list(self.agent_cache.keys())

    def get_cached_tools(self) -> list[str]:
        """Get list of cached tool names."""
        return list(self.tool_cache.keys())


_global_factory = AgentFactory()


def get_agent_factory() -> AgentFactory:
    """Get the global agent factory instance."""
    return _global_factory


def create_agent(agent_name: str, **overrides: Any) -> Agent | None:
    """Convenience function to create an agent using the global factory."""
    return _global_factory.create_agent(agent_name, **overrides)


def create_agents(agent_names: list[str], **overrides: Any) -> list[Agent]:
    """Convenience function to create multiple agents using the global factory."""
    return _global_factory.create_agents(agent_names, **overrides)


def create_agent_group(group_name: str, **overrides: Any) -> list[Agent]:
    """Convenience function to create an agent group using the global factory."""
    return _global_factory.create_agent_group(group_name, **overrides)
