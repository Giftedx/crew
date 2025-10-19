"""Tool for interacting with the Mem0 enhanced memory layer.

This tool provides a structured interface to a persistent, personalized memory
store powered by Mem0. It allows agents to:
- Add new memories (observations, facts, user preferences)
- Retrieve all memories for a user
- Search memories semantically
- Get a history of interactions

The tool is designed to be used within the CrewAI framework and respects the
project's tenancy and feature flag conventions. It will only be active if the
`ENABLE_ENHANCED_MEMORY` flag is set and a `MEM0_API_KEY` is available.
"""

from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field

from ..services.mem0_service import Mem0MemoryService
from ..step_result import StepResult
from ._base import BaseTool


class Mem0MemorySchema(BaseModel):
    action: Literal["remember", "recall", "update", "delete", "list", "history"] = (
        Field(..., description="The memory action to perform.")
    )
    content: Optional[str] = Field(
        None, description="The content to remember or update."
    )
    query: Optional[str] = Field(
        None, description="The query to recall relevant memories."
    )
    memory_id: Optional[str] = Field(
        None,
        description="The ID of the memory to update, delete, or retrieve history for.",
    )
    limit: Optional[int] = Field(
        10,
        description="Maximum number of memories to return for recall/list operations.",
    )


class Mem0MemoryTool(BaseTool):
    """A tool to manage persistent user preferences and learned patterns across sessions using Mem0."""

    name: str = "mem0_memory_tool"
    description: str = (
        "Manages persistent user preferences and learned patterns across sessions. "
        "Supports remembering user choices, recalling relevant preferences, and "
        "adapting to user behavior over time."
    )
    args_schema: type[BaseModel] = Mem0MemorySchema

    def _run(
        self,
        action: Literal["remember", "recall", "update", "delete", "list", "history"],
        tenant: str,
        workspace: str,
        content: Optional[str] = None,
        query: Optional[str] = None,
        memory_id: Optional[str] = None,
        limit: Optional[int] = 10,
    ) -> StepResult:
        """
        Execute the Mem0 memory operation.

        Args:
            action: The memory operation to perform.
            tenant: Tenant identifier for isolation.
            workspace: Workspace identifier.
            content: Content for remember/update operations.
            query: Query string for recall operations.
            memory_id: Memory ID for update/delete/history operations.
            limit: Maximum number of results for recall/list operations.

        Returns:
            StepResult with operation results or error.
        """
        mem0_service = Mem0MemoryService()
        user_id = f"{tenant}:{workspace}"

        if action == "remember":
            if not content:
                return StepResult.fail("Content must be provided to remember a memory.")
            metadata = {"tenant": tenant, "workspace": workspace}
            return mem0_service.remember(content, user_id, metadata)

        elif action == "recall":
            if not query:
                return StepResult.fail("A query must be provided to recall memories.")
            return mem0_service.recall(query, user_id, limit=limit or 10)

        elif action == "update":
            if not memory_id or not content:
                return StepResult.fail(
                    "Both memory_id and content must be provided to update a memory."
                )
            metadata = {"tenant": tenant, "workspace": workspace}
            return mem0_service.update_memory(memory_id, content, user_id, metadata)

        elif action == "delete":
            if not memory_id:
                return StepResult.fail("memory_id must be provided to delete a memory.")
            return mem0_service.delete_memory(memory_id, user_id)

        elif action == "list":
            return mem0_service.get_all_memories(user_id)

        elif action == "history":
            if not memory_id:
                return StepResult.fail(
                    "memory_id must be provided to retrieve memory history."
                )
            return mem0_service.get_memory_history(memory_id, user_id)

        else:
            return StepResult.fail(f"Unknown action: {action}")
