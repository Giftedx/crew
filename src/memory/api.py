"""Legacy-compatible memory API facade.

This module provides ``store/retrieve/prune/pin/archive`` functions under the
``memory.api`` import path expected by tests. It forwards most functionality to
``domains.memory.api`` but implements ``store`` locally to ensure compatibility
with the simple in-memory ``memory.vector_store`` record schema (which uses a
``payload`` field).
"""

from __future__ import annotations

import json
import tempfile
from platform.security.privacy import privacy_filter
from platform.time import default_utc_now

from archive import archive_file
from domains.memory import embeddings
from domains.memory.api import MemoryHit, pin, prune, retrieve  # re-export
from domains.memory.store import MemoryItem, MemoryStore

from . import vector_store


# Re-export selected types/functions for convenience
__all__ = ["MemoryHit", "archive", "pin", "prune", "retrieve", "store"]


def store(
    store: MemoryStore,
    vstore: vector_store.VectorStore,
    *,
    tenant: str,
    workspace: str,
    text: str,
    item_type: str = "long",
    policy: str = "default",
) -> int:
    """Store ``text`` and metadata in SQLite + vector store.

    Uses the lightweight in-memory vector record schema with a ``payload``
    field to remain compatible with tests that directly inspect payloads.
    """
    clean, _ = privacy_filter.filter_text(text, {"tenant": tenant})
    vec = embeddings.embed([clean])[0]
    now = default_utc_now().isoformat()
    item = MemoryItem(
        id=None,
        tenant=tenant,
        workspace=workspace,
        type=item_type,
        content_json=json.dumps({"text": clean}),
        embedding_json=json.dumps(vec),
        ts_created=now,
        ts_last_used=now,
        retention_policy=policy,
        decay_score=1.0,
        pinned=0,
        archived=0,
    )
    item_id = store.add_item(item)
    namespace = vector_store.VectorStore.namespace(tenant, workspace, "memory")
    vstore.upsert(namespace, [vector_store.VectorRecord(vector=vec, payload={"id": item_id, "text": clean})])
    return item_id


def archive(store: MemoryStore, item_id: int, *, tenant: str, workspace: str) -> None:
    item = store.get_item(item_id)
    if not item:
        return
    data = json.loads(item.content_json).get("text", "")
    with tempfile.NamedTemporaryFile("w", delete=False) as tmp:
        tmp.write(data)
        tmp.flush()
        archive_file(tmp.name, {"kind": "memory", "tenant": tenant, "workspace": workspace, "visibility": "private"})
    store.mark_archived(item_id)
