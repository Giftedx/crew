from memory.vector_store import VectorRecord, VectorStore


def test_vector_store_dimension_mismatch(monkeypatch):
    try:
        store = VectorStore()
    except RuntimeError:
        # qdrant-client optional; skip test gracefully if missing
        return

    store.upsert("tenant:ws:creator", [VectorRecord(vector=[0.1, 0.2, 0.3], payload={})])
    # Second upsert with different dimensionality should raise
    try:
        store.upsert("tenant:ws:creator", [VectorRecord(vector=[0.1, 0.2], payload={})])
    except ValueError as e:
        assert "Dimension mismatch" in str(e)
    else:  # pragma: no cover - logic failure
        raise AssertionError("Expected dimension mismatch error not raised")
