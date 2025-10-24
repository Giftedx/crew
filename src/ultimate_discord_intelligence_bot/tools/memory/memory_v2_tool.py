"""Memory V2 Tool - CrewAI tool for unified memory facade

This tool provides CrewAI agents with access to the unified memory facade,
enabling tenant-aware memory operations through the consolidated memory system.

See ADR-0002 for architectural decision rationale.
"""

from __future__ import annotations

import logging
from typing import Any

from crewai.tools import BaseTool  # type: ignore
from pydantic import BaseModel, Field

from ultimate_discord_intelligence_bot.memory import (
    UnifiedMemoryService,
    get_memory_namespace,
    get_unified_memory,
)
from ultimate_discord_intelligence_bot.step_result import StepResult


logger = logging.getLogger(__name__)


class MemoryV2OperationInput(BaseModel):
    """Input schema for memory V2 operations"""

    operation: str = Field(..., description="Operation: upsert, query, delete, get_stats")
    content: str | None = Field(default=None, description="Content for upsert operations")
    vector: list[float] | None = Field(default=None, description="Vector for query operations")
    metadata: dict[str, Any] | None = Field(default=None, description="Optional metadata")
    top_k: int = Field(default=10, description="Number of results for query operations")
    creator: str | None = Field(default=None, description="Creator identifier for namespace isolation")
    tenant: str = Field(default="default", description="Tenant identifier")
    workspace: str = Field(default="main", description="Workspace identifier")


class MemoryV2Tool(BaseTool):
    """CrewAI tool for unified memory facade operations."""

    name: str = "memory_v2_tool"
    description: str = (
        "Unified memory operations using the memory facade. "
        "Provides tenant-aware memory storage and retrieval with vector search. "
        "Operations: upsert, query, delete, get_stats. "
        "Supports semantic search and namespace isolation."
    )
    args_schema: type[BaseModel] = MemoryV2OperationInput

    def __init__(self) -> None:
        """Initialize the memory V2 tool."""
        super().__init__()
        self._memory: UnifiedMemoryService | None = None

    def _get_memory(self) -> UnifiedMemoryService:
        """Get unified memory service instance."""
        if self._memory is None:
            self._memory = get_unified_memory()
        return self._memory

    def _run(
        self,
        operation: str,
        content: str | None = None,
        vector: list[float] | None = None,
        metadata: dict[str, Any] | None = None,
        top_k: int = 10,
        creator: str | None = None,
        tenant: str = "default",
        workspace: str = "main",
        **kwargs: Any,
    ) -> str:
        """Execute memory operation using unified facade.

        Args:
            operation: Operation type (upsert, query, delete, get_stats)
            content: Content for upsert operations
            vector: Vector for query operations
            metadata: Optional metadata
            top_k: Number of results for queries
            creator: Creator identifier
            tenant: Tenant identifier
            workspace: Workspace identifier

        Returns:
            JSON string result of the operation
        """
        try:
            memory = self._get_memory()
            namespace = get_memory_namespace(tenant, workspace, creator or "default")

            if operation == "upsert":
                if not content:
                    import json

                    return json.dumps(StepResult.fail("Content required for upsert operation").to_dict())

                records = [{"content": content, "metadata": metadata or {}}]
                import asyncio

                result = asyncio.run(memory.upsert(namespace, records, creator or "default"))
                import json

                return json.dumps(result.to_dict())

            elif operation == "query":
                if not vector:
                    import json

                    return json.dumps(StepResult.fail("Vector required for query operation").to_dict())

                import asyncio

                result = asyncio.run(memory.query(namespace, vector, top_k, creator or "default"))
                import json

                return json.dumps(result.to_dict())

            elif operation == "delete":
                # Memory facade doesn't expose delete directly, return not supported
                import json

                return json.dumps(StepResult.fail("Delete operation not supported in current facade").to_dict())

            elif operation == "get_stats":
                # Get memory statistics for the namespace
                import asyncio

                stats = asyncio.run(memory.get_stats(namespace))
                import json

                return json.dumps(StepResult.ok(data=stats).to_dict())

            else:
                import json

                return json.dumps(StepResult.fail(f"Unknown operation: {operation}").to_dict())

        except Exception as exc:
            logger.error(f"Memory V2 operation failed: {exc}", exc_info=True)
            import json

            return json.dumps(StepResult.fail(f"Memory operation failed: {exc}").to_dict())
