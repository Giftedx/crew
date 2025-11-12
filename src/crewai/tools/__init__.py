"""Compatibility module for crewai.tools imports."""

from abc import ABC, abstractmethod
from typing import Any, Optional

from pydantic import BaseModel, Field


class EnvVar(BaseModel):
    """Environment variable configuration for tools."""

    name: str = Field(..., description="Name of the environment variable")
    description: str = Field(..., description="Description of what this variable is used for")
    required: bool = Field(default=True, description="Whether this variable is required")
    default: str | None = Field(default=None, description="Default value if not required")


class BaseTool(ABC):
    """Base tool class compatible with crewai.tools.BaseTool interface."""

    name: str
    description: str

    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)

    @abstractmethod
    def run(self, *args, **kwargs) -> Any:
        """Run the tool with given arguments."""

    def _run(self, *args, **kwargs) -> Any:
        """Internal run method - can be overridden by subclasses."""
        return self.run(*args, **kwargs)


__all__ = ["BaseTool", "EnvVar"]
