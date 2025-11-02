"""Base agent class for the Ultimate Discord Intelligence Bot.

This module provides the foundation for all agent implementations,
ensuring consistent patterns and testability.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from crewai import Agent  # type: ignore[import-untyped]
from ultimate_discord_intelligence_bot.crewai_tool_wrappers import wrap_tool_for_crewai


if TYPE_CHECKING:
    from ultimate_discord_intelligence_bot.tools._base import BaseTool


class BaseAgent(ABC):
    """Base class for all agent implementations.

    Provides consistent patterns for agent creation, tool registration,
    and configuration management.
    """

    def __init__(self, tools: list[BaseTool] | None = None):
        """Initialize the agent with optional tools.

        Args:
            tools: List of tools to register with this agent
        """
        self._tools = tools or []

    @property
    @abstractmethod
    def role(self) -> str:
        """Agent role description."""

    @property
    @abstractmethod
    def goal(self) -> str:
        """Agent goal description."""

    @property
    @abstractmethod
    def backstory(self) -> str:
        """Agent backstory description."""

    @property
    def verbose(self) -> bool:
        """Whether agent should be verbose."""
        return True

    @property
    def allow_delegation(self) -> bool:
        """Whether agent can delegate to other agents."""
        return False

    def add_tool(self, tool: BaseTool) -> None:
        """Add a tool to this agent.

        Args:
            tool: Tool to add
        """
        self._tools.append(tool)

    def create(self) -> Agent:
        """Create a CrewAI Agent instance.

        Returns:
            Configured CrewAI Agent
        """
        wrapped_tools = [wrap_tool_for_crewai(tool) for tool in self._tools]

        return Agent(
            role=self.role,
            goal=self.goal,
            backstory=self.backstory,
            tools=wrapped_tools,
            verbose=self.verbose,
            allow_delegation=self.allow_delegation,
        )
