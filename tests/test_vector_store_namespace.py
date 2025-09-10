from __future__ import annotations

from memory.vector_store import VectorRecord, VectorStore


def test_vector_store_namespace_and_physical_mapping():
    # Default settings use an in-memory dummy Qdrant client
    store = VectorStore()

    ns = VectorStore.namespace("tenant", "ws", "creator")
    assert ns == "tenant:ws:creator"

    # Upsert one point and ensure collection exists with sanitized physical name
    store.upsert(ns, [VectorRecord(vector=[0.1, 0.2, 0.3], payload={"text": "t"})])

    physical = store._physical_names.get(ns)
    assert physical == "tenant__ws__creator"

    # Check dummy client collections contain the physical name
    cols = [c.name for c in store.client.get_collections().collections]
    assert physical in cols
