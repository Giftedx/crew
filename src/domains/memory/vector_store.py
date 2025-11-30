"""Vector store implementation for memory operations.

This module provides the `VectorStore` class for managing vector embeddings,
supporting operations like upserting records and querying by similarity or text.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any


if TYPE_CHECKING:
    from collections.abc import Sequence


logger = logging.getLogger(__name__)


@dataclass
class VectorRecord:
    """A vector record with content and metadata.

    Attributes:
        content: The text content of the record.
        metadata: Dictionary containing metadata (e.g., source, timestamp).
        vector: The embedding vector (list of floats).
        id: Unique identifier for the record (optional).
    """

    content: str
    metadata: dict[str, Any]
    vector: list[float] | None = None
    id: str | None = None


class VectorStore:
    """Vector store for memory operations.

    Manages a collection of vector records, allowing for storage and retrieval.
    Currently implements a simple in-memory store, but designed to be extended
    or replaced with a persistent backend (like Qdrant).
    """

    def __init__(self):
        """Initialize vector store."""
        self._collections: dict[str, list[VectorRecord]] = {}
        logger.info("VectorStore initialized")

    @staticmethod
    def namespace(tenant: str, workspace: str, creator: str = "default") -> str:
        """Generate namespace for tenant/workspace/creator.

        Args:
            tenant: Tenant identifier.
            workspace: Workspace identifier.
            creator: Creator identifier (default "default").

        Returns:
            str: Colon-separated namespace string.
        """
        return f"{tenant}:{workspace}:{creator}"

    def upsert(self, namespace: str, records: Sequence[VectorRecord]) -> None:
        """Upsert records into the collection.

        Args:
            namespace: The namespace to store records in.
            records: A sequence of VectorRecord objects to insert/update.
        """
        if namespace not in self._collections:
            self._collections[namespace] = []

        self._collections[namespace].extend(records)
        logger.info(f"Upserted {len(records)} records to {namespace}")

    def query(self, namespace: str, vector: Sequence[float], top_k: int = 3) -> list[VectorRecord]:
        """Query similar vectors from the collection.

        Args:
            namespace: The namespace to query.
            vector: The query vector.
            top_k: Number of results to return.

        Returns:
            list[VectorRecord]: Top K similar records.
        """
        if namespace not in self._collections:
            return []

        # Simple implementation - return first top_k records
        # Real implementation would compute cosine similarity
        return self._collections[namespace][:top_k]

    def search(self, namespace: str, query: str, limit: int = 10) -> list[VectorRecord]:
        """Search records by text query.

        Args:
            namespace: The namespace to search.
            query: The text query string.
            limit: Maximum number of results.

        Returns:
            list[VectorRecord]: Matching records.
        """
        if namespace not in self._collections:
            return []

        # Simple text search implementation
        results = []
        for record in self._collections[namespace]:
            if query.lower() in record.content.lower():
                results.append(record)
                if len(results) >= limit:
                    break

        return results


# Backward compatibility: Re-export MemoryService from its new location
# Note: Import moved to TYPE_CHECKING to break circular dependency
# Consumers should import from ultimate_discord_intelligence_bot.services.memory_service directly
# from ultimate_discord_intelligence_bot.services.memory_service import MemoryService


__all__ = ["VectorRecord", "VectorStore"]
