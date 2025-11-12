"""Compatibility shim for GraphMemoryTool."""

from pydantic import BaseModel

from domains.memory.vector.graph_memory_tool import GraphMemoryTool


# Stub for test compatibility - schema not implemented in actual tool
class GraphMemorySchema(BaseModel):
    """Schema for graph memory operations (stub for test compatibility)."""


__all__ = ["GraphMemorySchema", "GraphMemoryTool"]
