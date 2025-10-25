"""Agent registry for the Ultimate Discord Intelligence Bot.

This module provides a registry pattern for agent discovery and management,
enabling dynamic agent loading and testing.
"""

from __future__ import annotations

from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from .base import BaseAgent


# Global agent registry
AGENT_REGISTRY: dict[str, type[BaseAgent]] = {}


def register_agent(name: str):
    """Decorator to register an agent class.

    Args:
        name: Unique name for the agent

    Returns:
        Decorator function
    """

    def decorator(cls: type[BaseAgent]) -> type[BaseAgent]:
        """Register the agent class."""
        AGENT_REGISTRY[name] = cls
        return cls

    return decorator


def get_agent(name: str) -> type[BaseAgent] | None:
    """Get an agent class by name.

    Args:
        name: Agent name

    Returns:
        Agent class or None if not found
    """
    return AGENT_REGISTRY.get(name)


def list_agents() -> List[str]:
    """List all registered agent names.

    Returns:
        List of agent names
    """
    return list(AGENT_REGISTRY.keys())
