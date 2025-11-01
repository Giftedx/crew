"""Universal tool system for multi-framework compatibility.

This package provides abstractions for creating tools that work across
multiple AI frameworks (CrewAI, LangGraph, AutoGen, LlamaIndex).
"""

from __future__ import annotations

from ai.frameworks.tools.converters import BaseUniversalTool
from ai.frameworks.tools.protocols import ParameterSchema, ToolMetadata, UniversalTool


__all__ = [
    "UniversalTool",
    "BaseUniversalTool",
    "ParameterSchema",
    "ToolMetadata",
]
