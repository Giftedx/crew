"""Compatibility shim for Mem0MemoryTool."""

from pydantic import BaseModel

from ultimate_discord_intelligence_bot.tools._base import BaseTool


# Stub for test compatibility - tool not yet implemented
class Mem0MemorySchema(BaseModel):
    """Schema for Mem0 memory operations (stub for test compatibility)."""


class Mem0MemoryTool(BaseTool):
    """Stub implementation of Mem0 memory tool for test compatibility."""

    name: str = "mem0_memory_tool"
    description: str = "Mem0 memory tool (stub implementation)"

    def _run(self, *args, **kwargs):
        """Stub implementation."""
        return {"status": "stub_implementation", "message": "Mem0MemoryTool not yet implemented"}


__all__ = ["Mem0MemorySchema", "Mem0MemoryTool"]
