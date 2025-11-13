"""Compatibility module for crewai.tools imports.

This module provides backward compatibility for code that imports from crewai.tools.
All tools should actually import from the main crewai module.

Note: The system CrewAI library has circular import issues, so we provide stub classes here.
"""

from typing import Any, Optional, Union

from pydantic import BaseModel, Field


class BaseTool(BaseModel):
    """Stub BaseTool class for compatibility."""

    name: str
    description: str

    def run(self, *args, **kwargs) -> Any:
        """Stub run method."""
        raise NotImplementedError("This is a stub implementation")


class Agent(BaseModel):
    """Stub Agent class for compatibility."""

    role: str
    goal: str
    backstory: str
    tools: list[BaseTool] | None = None

    def __init__(self, **data):
        super().__init__(**data)


class Task(BaseModel):
    """Stub Task class for compatibility."""

    description: str
    expected_output: str
    agent: Agent | None = None

    def __init__(self, **data):
        super().__init__(**data)


class Process:
    """Stub Process enum for compatibility."""

    SEQUENTIAL = "sequential"
    HIERARCHICAL = "hierarchical"

    # Add lowercase aliases for compatibility
    sequential = SEQUENTIAL
    hierarchical = HIERARCHICAL


class Crew(BaseModel):
    """Stub Crew class for compatibility."""

    agents: list[Agent]
    tasks: list[Task]
    process: str = Process.SEQUENTIAL

    def __init__(self, **data):
        super().__init__(**data)

    def kickoff(self) -> dict[str, Any]:
        """Stub kickoff method."""
        return {"result": "Stub implementation - CrewAI library has circular import issues"}


class EnvVar(BaseModel):
    """Environment variable configuration for tools."""

    name: str = Field(..., description="Name of the environment variable")
    description: str = Field(..., description="Description of what this variable is used for")
    required: bool = Field(default=True, description="Whether this variable is required")
    default: str | None = Field(default=None, description="Default value if not required")


__all__ = ["Agent", "BaseTool", "Crew", "EnvVar", "Process", "Task"]
