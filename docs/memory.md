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

## Related Optimizations

For improved retrieval efficiency and lower token costs, see:

- [Prompt Compression](prompt_compression.md) – Reduces prompt token footprint before routing, preserving salient context while lowering cost.
- [Semantic Cache](semantic_cache.md) – Skips redundant model calls by reusing high-similarity prior responses (with similarity bucketing & prefetch metrics).

These layers are complementary: compression minimizes outgoing request size, while the semantic cache can eliminate the request entirely for near-duplicate intents.
