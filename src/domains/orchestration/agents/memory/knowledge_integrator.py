"""Knowledge Integrator Agent.

This agent preserves mission intelligence across memory systems.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from domains.orchestration.agents.base import BaseAgent
from domains.orchestration.agents.registry import register_agent
from ultimate_discord_intelligence_bot.tools import (
    GraphMemoryTool,
    HippoRagContinualMemoryTool,
    MemoryCompactionTool,
    MemoryStorageTool,
    MultimodalAnalysisTool,
    RagHybridTool,
    RagIngestTool,
    RagIngestUrlTool,
    VectorSearchTool,
)


if TYPE_CHECKING:
    from ultimate_discord_intelligence_bot.tools._base import BaseTool


@register_agent("knowledge_integrator")
class KnowledgeIntegratorAgent(BaseAgent):
    """Knowledge Integrator Agent for memory management and storage."""

    def __init__(self):
        """Initialize the knowledge integrator with its tools."""
        tools = self._get_memory_tools()
        super().__init__(tools)

    @property
    def role(self) -> str:
        """Agent role."""
        return "Knowledge Integration Steward"

    @property
    def goal(self) -> str:
        """Agent goal."""
        return "Preserve mission intelligence across memory systems."

    @property
    def backstory(self) -> str:
        """Agent backstory."""
        return "Knowledge architecture with multimodal memory integration."

    @property
    def allow_delegation(self) -> bool:
        """No delegation for knowledge integrator."""
        return False

    def _get_memory_tools(self) -> list[BaseTool]:
        """Get memory tools for knowledge management."""
        from domains.memory.embeddings import embed

        def embedding_function(text: str) -> list[float]:
            """Convert text to embedding vector using the core embeddings module."""
            try:
                return embed([text])[0]
            except Exception:
                import hashlib

                hash_val = int(hashlib.md5(text.encode(), usedforsecurity=False).hexdigest()[:8], 16)
                return [float((hash_val + i) % 1000) / 1000.0 for i in range(384)]

        return [
            MemoryStorageTool(embedding_fn=embedding_function),
            GraphMemoryTool(),
            HippoRagContinualMemoryTool(),
            MemoryCompactionTool(),
            RagIngestTool(),
            RagIngestUrlTool(),
            RagHybridTool(),
            VectorSearchTool(),
            MultimodalAnalysisTool(),
        ]
