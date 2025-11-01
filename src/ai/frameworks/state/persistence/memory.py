"""In-memory state persistence backend for testing and development."""

from copy import deepcopy

import structlog


logger = structlog.get_logger(__name__)


class MemoryBackend:
    """In-memory storage backend for workflow state.

    This backend stores state in memory and is suitable for testing,
    development, and short-lived workflows. State is lost when the
    process terminates.

    Attributes:
        _storage: Dictionary mapping workflow IDs to serialized state
    """

    def __init__(self) -> None:
        """Initialize the memory backend."""
        self._storage: dict[str, dict] = {}
        logger.info("memory_backend_initialized")

    async def save(self, workflow_id: str, state: dict) -> None:
        """Save state to memory.

        Args:
            workflow_id: Unique identifier for the workflow
            state: Serialized state dictionary
        """
        self._storage[workflow_id] = deepcopy(state)  # Deep copy to avoid reference issues
        logger.info("state_saved", workflow_id=workflow_id, backend="memory")

    async def load(self, workflow_id: str) -> dict | None:
        """Load state from memory.

        Args:
            workflow_id: Unique identifier for the workflow

        Returns:
            Serialized state dictionary or None if not found
        """
        state = self._storage.get(workflow_id)
        if state:
            logger.info("state_loaded", workflow_id=workflow_id, backend="memory")
            return deepcopy(state)  # Deep copy to avoid reference issues
        else:
            logger.warning("state_not_found", workflow_id=workflow_id, backend="memory")
            return None

    async def delete(self, workflow_id: str) -> bool:
        """Delete state from memory.

        Args:
            workflow_id: Unique identifier for the workflow

        Returns:
            True if deleted, False if not found
        """
        if workflow_id in self._storage:
            del self._storage[workflow_id]
            logger.info("state_deleted", workflow_id=workflow_id, backend="memory")
            return True
        else:
            logger.warning("state_not_found_for_delete", workflow_id=workflow_id, backend="memory")
            return False

    async def list_workflows(self) -> list[str]:
        """List all workflow IDs in memory.

        Returns:
            List of workflow IDs
        """
        workflows = list(self._storage.keys())
        logger.info("workflows_listed", count=len(workflows), backend="memory")
        return workflows

    def clear(self) -> None:
        """Clear all stored state (useful for testing)."""
        count = len(self._storage)
        self._storage.clear()
        logger.info("storage_cleared", count=count, backend="memory")
