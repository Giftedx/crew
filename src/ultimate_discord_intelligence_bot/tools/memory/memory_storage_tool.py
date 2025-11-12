"""Compatibility shim for MemoryStorageTool."""

from pydantic import BaseModel

from domains.memory.vector.memory_storage_tool import MemoryStorageTool


# Stub for test compatibility - schema not in actual tool
class MemoryStorageSchema(BaseModel):
    """Schema for memory storage operations (stub for test compatibility)."""


__all__ = ["MemoryStorageSchema", "MemoryStorageTool"]
