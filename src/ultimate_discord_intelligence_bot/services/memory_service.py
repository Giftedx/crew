"""Simple in-memory retrieval service.

The :class:`MemoryService` provides a minimal interface for storing and
retrieving snippets of text.  It acts as a stand-in for a full vector database
so components can integrate memory lookups without requiring heavy
infrastructure during testing.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class MemoryService:
    """Store and retrieve small text memories."""

    memories: List[Dict[str, str]] = field(default_factory=list)

    def add(self, text: str, metadata: Dict[str, str] | None = None) -> None:
        self.memories.append({"text": text, "metadata": metadata or {}})

    def retrieve(self, query: str, limit: int = 5) -> List[Dict[str, str]]:
        results = [m for m in self.memories if query.lower() in m["text"].lower()]
        return results[:limit]
