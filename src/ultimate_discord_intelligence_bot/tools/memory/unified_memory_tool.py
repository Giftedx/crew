"""Compatibility shim for ultimate_discord_intelligence_bot.tools.memory.unified_memory_tool

Re-exports UnifiedMemoryTool from its new location in domains.memory.vector.
"""

from domains.memory.vector.unified_memory_tool import (
    UnifiedContextTool,
    UnifiedMemoryStoreTool,
    UnifiedMemoryTool,
)


__all__ = ["UnifiedContextTool", "UnifiedMemoryStoreTool", "UnifiedMemoryTool"]
