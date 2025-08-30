"""Lightweight evidence retriever that wraps the unified memory API."""

from __future__ import annotations

from dataclasses import dataclass

from memory import api as memory_api
from memory import vector_store
from memory.store import MemoryStore

from .schema import Evidence


@dataclass
class EvidencePack:
    snippets: list[Evidence]


def gather(  # noqa: PLR0913 - explicit parameter list clearer than packing into config object
    mstore: MemoryStore,
    vstore: vector_store.VectorStore,
    *,
    tenant: str,
    workspace: str,
    query: str,
    k: int = 3,
) -> EvidencePack:
    """Retrieve ``k`` evidence snippets from memory for ``query``."""

    hits = memory_api.retrieve(mstore, vstore, tenant=tenant, workspace=workspace, query=query, k=k)
    snippets = [
        Evidence(
            source_type="memory",
            locator={"id": h.id},
            quote=h.text,
            confidence=h.score,
        )
        for h in hits
    ]
    return EvidencePack(snippets)


__all__ = ["gather", "EvidencePack"]
