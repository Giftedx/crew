from memory import api, vector_store
from memory.store import MemoryStore, RetentionPolicy


def test_store_retrieve_and_prune(monkeypatch, tmp_path):
    mstore = MemoryStore(path=tmp_path / "mem.db")
    vstore = vector_store.VectorStore()
    mstore.upsert_policy(RetentionPolicy(name="short", tenant="t", ttl_days=0))

    item_id = api.store(mstore, vstore, tenant="t", workspace="w", text="hello world", policy="short")

    hits = api.retrieve(mstore, vstore, tenant="t", workspace="w", query="hello")
    assert any(h.id == item_id for h in hits)

    api.pin(mstore, item_id)
    assert api.prune(mstore, tenant="t") == 0

    api.pin(mstore, item_id, pinned=False)
    assert api.prune(mstore, tenant="t") == 1


def test_archive_marks_item(monkeypatch, tmp_path):
    called = {}

    def fake_archive(path, meta):
        called["path"] = path
        called["meta"] = meta

    monkeypatch.setattr("memory.api.archive_file", fake_archive)
    mstore = MemoryStore(path=tmp_path / "mem.db")
    vstore = vector_store.VectorStore()
    item_id = api.store(mstore, vstore, tenant="t", workspace="w", text="data")
    api.archive(mstore, item_id, tenant="t", workspace="w")
    assert called["meta"]["kind"] == "memory"
    assert mstore.get_item(item_id).archived == 1
