# Unified Memory Layer

The unified memory layer normalises short and long term data into a single
SQLite/Qdrant backed store.  Items are recorded with retention policies and
optionally pinned or archived to the Discord CDN.

## Usage

```python
from memory import api, store, vector_store

mstore = store.MemoryStore()
vstore = vector_store.VectorStore()

item_id = api.store(
    mstore,
    vstore,
    tenant="default",
    workspace="main",
    text="Hello world",
    policy="ephemeral",
)

hits = api.retrieve(
    mstore, vstore, tenant="default", workspace="main", query="hello"
)
```

Retention policies are configured per tenant and enforced via
`api.prune`.  Items can be `pin`ned to avoid pruning or `archive`d to the
Discord CDN via the archiver facade.
