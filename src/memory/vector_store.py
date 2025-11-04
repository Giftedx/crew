"""Legacy-compatible in-memory VectorStore implementation for tests.

This module provides a minimal VectorStore API expected by unit tests that
previously imported ``memory.vector_store``. It intentionally avoids any
external dependencies (like qdrant-client) and simulates the required
behaviors:

- Namespace helper with ``tenant:ws:creator`` string format
- Dimension enforcement per-collection (raises ValueError on mismatch)
- Physical name mapping (``tenant__ws__creator``) exposed via ``_physical_names``
- A lightweight ``client`` stub with ``get_collections().collections``

It is not intended for production use.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class VectorRecord:
    """A vector record with optional payload and id.

    Tests pass ``vector=[...], payload={}``. We keep fields permissive
    and avoid additional validation.
    """

    vector: list[float]
    payload: dict[str, Any] | None = None
    id: str | None = None


class _CollectionRef:
    def __init__(self, name: str) -> None:
        self.name = name


class _CollectionsEnvelope:
    def __init__(self, names: list[str]) -> None:
        self.collections = [_CollectionRef(n) for n in names]


class _DummyClient:
    def __init__(self, get_names_callable):
        self._get_names_callable = get_names_callable

    def get_collections(self) -> _CollectionsEnvelope:  # pragma: no cover - trivial
        return _CollectionsEnvelope(self._get_names_callable())


class VectorStore:
    """A very small in-memory vector store with test-focused features."""

    def __init__(self) -> None:
        self._collections: dict[str, list[VectorRecord]] = {}
        self._dimensions: dict[str, int] = {}
        self._physical_names: dict[str, str] = {}

        # Expose a tiny client with get_collections() API
        self.client = _DummyClient(lambda: list(self._collections.keys()))

    @staticmethod
    def namespace(tenant: str, workspace: str, creator: str = "default") -> str:
        return f"{tenant}:{workspace}:{creator}"

    @staticmethod
    def _physical(ns: str) -> str:
        # Simple sanitization for tests: replace ':' with '__'
        return ns.replace(":", "__")

    def upsert(self, namespace: str, records: list[VectorRecord]) -> None:
        physical = self._physical_names.setdefault(namespace, self._physical(namespace))
        # Ensure collection exists
        col = self._collections.setdefault(physical, [])

        # Enforce consistent dimensionality per-collection
        for rec in records:
            if rec.vector is None:
                continue
            dim = len(rec.vector)
            if physical in self._dimensions:
                exp = self._dimensions[physical]
                if dim != exp:
                    raise ValueError(f"Dimension mismatch: expected {exp}, got {dim}")
            else:
                self._dimensions[physical] = dim
        col.extend(records)

    # Additional helpers used by other tests (kept no-op/simple here)
    def query(self, namespace: str, vector: list[float], top_k: int = 3) -> list[VectorRecord]:  # pragma: no cover
        physical = self._physical_names.get(namespace, self._physical(namespace))
        return self._collections.get(physical, [])[:top_k]

    def search(self, namespace: str, query: str, limit: int = 10) -> list[VectorRecord]:  # pragma: no cover
        physical = self._physical_names.get(namespace, self._physical(namespace))
        results: list[VectorRecord] = []
        for r in self._collections.get(physical, []):
            text = ""
            payload = r.payload or {}
            try:
                text = str(payload.get("text", ""))
            except Exception:
                text = ""
            if query.lower() in text.lower():
                results.append(r)
                if len(results) >= limit:
                    break
        return results


__all__ = ["VectorRecord", "VectorStore"]
