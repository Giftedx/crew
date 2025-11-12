"""Compatibility module for crewai.tools imports.

This module provides backward compatibility for code that imports from crewai.tools.
All tools should actually import from the main crewai module.
"""

# Import from parent module for re-export

from pydantic import BaseModel, Field

from crewai import BaseTool


class EnvVar(BaseModel):
    """Environment variable configuration for tools."""

    name: str = Field(..., description="Name of the environment variable")
    description: str = Field(..., description="Description of what this variable is used for")
    required: bool = Field(default=True, description="Whether this variable is required")
    default: str | None = Field(default=None, description="Default value if not required")


__all__ = ["BaseTool", "EnvVar"]
