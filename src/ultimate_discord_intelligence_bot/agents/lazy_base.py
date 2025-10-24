"""Lazy Agent Base Class.

This module provides a lazy loading base class for agents that defers tool
instantiation until the tools are actually needed, reducing startup time.
"""

from __future__ import annotations

from typing import Any

from ultimate_discord_intelligence_bot.agents.base import BaseAgent
from ultimate_discord_intelligence_bot.tools._base import BaseTool
from ultimate_discord_intelligence_bot.tools.lazy_loader import LazyToolWrapper, create_lazy_tool_wrapper


class LazyBaseAgent(BaseAgent):
    """Base agent class with lazy tool loading."""

    def __init__(self, tool_specs: list[dict[str, Any]] | None = None):
        """Initialize the lazy agent with tool specifications."""
        self._tool_specs = tool_specs or []
        self._lazy_tools: LazyToolWrapper | None = None

        # Initialize with empty tools list - tools will be loaded lazily
        super().__init__(tools=[])

    @property
    def tools(self) -> list[BaseTool]:
        """Get tools, loading them lazily on first access."""
        if self._lazy_tools is None:
            self._lazy_tools = create_lazy_tool_wrapper(self._tool_specs)

        return self._lazy_tools.tools

    def preload_tools(self) -> dict[str, bool]:
        """Preload all tools and return success status."""
        if self._lazy_tools is None:
            self._lazy_tools = create_lazy_tool_wrapper(self._tool_specs)

        return self._lazy_tools.preload()

    def get_tool_loading_stats(self) -> dict[str, Any]:
        """Get tool loading statistics."""
        if self._lazy_tools is None:
            return {"status": "not_loaded", "tools": 0}

        stats = self._lazy_tools.get_stats()
        stats["tool_specs_count"] = len(self._tool_specs)
        return stats

    def _get_tool_specs(self) -> list[dict[str, Any]]:
        """Get tool specifications for this agent. Override in subclasses."""
        return []

    def _initialize_tool_specs(self):
        """Initialize tool specifications if not already set."""
        if not self._tool_specs:
            self._tool_specs = self._get_tool_specs()


class LazyAgentMixin:
    """Mixin for adding lazy loading capabilities to existing agents."""

    def __init__(self, *args, **kwargs):
        """Initialize the mixin."""
        super().__init__(*args, **kwargs)
        self._lazy_tools: LazyToolWrapper | None = None
        self._original_tools = self._tools.copy()

    def _enable_lazy_loading(self, tool_specs: list[dict[str, Any]]):
        """Enable lazy loading for this agent."""
        self._lazy_tools = create_lazy_tool_wrapper(tool_specs)
        # Replace tools with lazy wrapper
        self._tools = []

    @property
    def tools(self) -> list[BaseTool]:
        """Get tools with lazy loading support."""
        if self._lazy_tools is not None:
            return self._lazy_tools.tools
        return self._original_tools

    def preload_tools(self) -> dict[str, bool]:
        """Preload tools if lazy loading is enabled."""
        if self._lazy_tools is not None:
            return self._lazy_tools.preload()
        return {"status": "not_lazy_loaded"}

    def get_tool_loading_stats(self) -> dict[str, Any]:
        """Get tool loading statistics."""
        if self._lazy_tools is not None:
            return self._lazy_tools.get_stats()
        return {"status": "not_lazy_loaded", "tools": len(self._original_tools)}


def convert_agent_to_lazy(agent: BaseAgent, tool_specs: list[dict[str, Any]]) -> LazyBaseAgent:
    """Convert an existing agent to use lazy loading."""
    lazy_agent = LazyBaseAgent(tool_specs)

    # Copy agent properties
    lazy_agent._role = getattr(agent, "_role", agent.role)
    lazy_agent._goal = getattr(agent, "_goal", agent.goal)
    lazy_agent._backstory = getattr(agent, "_backstory", agent.backstory)
    lazy_agent._allow_delegation = getattr(agent, "_allow_delegation", agent.allow_delegation)

    return lazy_agent


def create_lazy_tool_spec(tool_name: str, *args, **kwargs) -> dict[str, Any]:
    """Create a tool specification for lazy loading."""
    return {"name": tool_name, "args": list(args), "kwargs": kwargs}


def create_lazy_tool_specs(tool_names: list[str]) -> list[dict[str, Any]]:
    """Create tool specifications for a list of tool names."""
    return [create_lazy_tool_spec(name) for name in tool_names]
