from __future__ import annotations

from platform.core.step_result import StepResult

from mem0 import Memory

from ..settings import _get_setting


class Mem0MemoryService:
    """Service wrapper for Mem0 to manage user preferences and learned patterns."""

    def __init__(self):
        """Initializes the Mem0MemoryService."""
        qdrant_url = _get_setting("QDRANT_URL", "http://localhost:6333")
        self.memory = Memory(config={"vector_store": {"provider": "qdrant", "config": {"url": qdrant_url}}})

    def remember(self, content: str, user_id: str, metadata: dict | None = None) -> StepResult:
        """
        Stores a memory or preference for a user.

        Args:
            content: The text content of the memory to store.
            user_id: The unique identifier for the user.
            metadata: Optional metadata to associate with the memory.

        Returns:
            A StepResult indicating success or failure.
        """
        try:
            result = self.memory.add(content, user_id=user_id, metadata=metadata or {})
            return StepResult.ok(data=result)
        except Exception as e:
            return StepResult.fail(f"Mem0 remember failed: {e}")

    def recall(self, query: str, user_id: str, limit: int = 10) -> StepResult:
        """
        Recalls memories or preferences for a user based on a query.

        Args:
            query: The query to search for relevant memories.
            user_id: The unique identifier for the user.
            limit: Maximum number of memories to return.

        Returns:
            A StepResult containing the search results.
        """
        try:
            results = self.memory.search(query, user_id=user_id, limit=limit)
            return StepResult.ok(data=results)
        except Exception as e:
            return StepResult.fail(f"Mem0 recall failed: {e}")

    def update_memory(self, memory_id: str, content: str, user_id: str, metadata: dict | None = None) -> StepResult:
        """
        Updates an existing memory.

        Args:
            memory_id: The ID of the memory to update.
            content: The new content for the memory.
            user_id: The unique identifier for the user.
            metadata: Optional metadata to update.

        Returns:
            A StepResult indicating success or failure.
        """
        try:
            result = self.memory.update(memory_id=memory_id, data=content, user_id=user_id, metadata=metadata or {})
            return StepResult.ok(data=result)
        except Exception as e:
            return StepResult.fail(f"Mem0 update failed: {e}")

    def delete_memory(self, memory_id: str, user_id: str) -> StepResult:
        """
        Deletes a specific memory.

        Args:
            memory_id: The ID of the memory to delete.
            user_id: The unique identifier for the user.

        Returns:
            A StepResult indicating success or failure.
        """
        try:
            self.memory.delete(memory_id=memory_id, user_id=user_id)
            return StepResult.ok(data={"deleted": memory_id})
        except Exception as e:
            return StepResult.fail(f"Mem0 delete failed: {e}")

    def get_all_memories(self, user_id: str) -> StepResult:
        """
        Retrieves all memories for a user.

        Args:
            user_id: The unique identifier for the user.

        Returns:
            A StepResult containing all memories for the user.
        """
        try:
            results = self.memory.get_all(user_id=user_id)
            return StepResult.ok(data=results)
        except Exception as e:
            return StepResult.fail(f"Mem0 get_all failed: {e}")

    def get_memory_history(self, memory_id: str, user_id: str) -> StepResult:
        """
        Retrieves the history of changes to a specific memory.

        Args:
            memory_id: The ID of the memory.
            user_id: The unique identifier for the user.

        Returns:
            A StepResult containing the memory history.
        """
        try:
            history = self.memory.history(memory_id=memory_id, user_id=user_id)
            return StepResult.ok(data=history)
        except Exception as e:
            return StepResult.fail(f"Mem0 history retrieval failed: {e}")
