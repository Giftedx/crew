import os
import time

from ultimate_discord_intelligence_bot.tools.memory_compaction_tool import (
    MemoryCompactionTool,
)
from ultimate_discord_intelligence_bot.tools.memory_storage_tool import (
    MemoryStorageTool,
)


def _set_flags(tmp_enable_ttl=True):
    os.environ["ENABLE_MEMORY_TTL"] = "1" if tmp_enable_ttl else "0"
    os.environ["MEMORY_TTL_SECONDS"] = "1"  # short TTL for tests
    os.environ["ENABLE_MEMORY_COMPACTION"] = "1"
    os.environ["QDRANT_URL"] = ":memory:"


def test_compaction_deletes_expired_points(monkeypatch):
    _set_flags()
    # Use default in-memory client via provider with multi-dimension embedding
    # (Fix #6: single-dimension vectors are rejected for semantic search integrity)
    store = MemoryStorageTool(collection="test_compact", embedding_fn=lambda t: [0.1, 0.2, 0.3])

    # Insert two items: one already expired, one fresh
    now = int(time.time())
    expired_payload = {"foo": "bar", "created_at": now - 10, "_ttl": 5}
    fresh_payload = {"foo": "baz", "created_at": now, "_ttl": 60}

    r1 = store.run(text="expired", metadata=expired_payload, collection="test_compact")
    assert r1.success
    r2 = store.run(text="fresh", metadata=fresh_payload, collection="test_compact")
    assert r2.success

    tool = MemoryCompactionTool(collection="test_compact")
    res = tool.run(collection="test_compact")
    assert res.success
    # Should have deleted exactly one
    assert res.data.get("deleted") == 1


def test_compaction_noop_when_disabled(monkeypatch):
    _set_flags(tmp_enable_ttl=True)
    os.environ["ENABLE_MEMORY_COMPACTION"] = "0"
    tool = MemoryCompactionTool(collection="test_compact2")
    res = tool.run(collection="test_compact2")
    assert res["status"] == "skipped"
