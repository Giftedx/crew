# Memory Examples

### Pinning and Pruning

```python
from memory import api, store, vector_store
from datetime import datetime, timedelta

mstore = store.MemoryStore()
vstore = vector_store.VectorStore()
mstore.upsert_policy(store.RetentionPolicy(name="short", tenant="t", ttl_days=1))

item = api.store(mstore, vstore, tenant="t", workspace="w", text="temp", policy="short")
api.pin(mstore, item)

# nothing pruned due to pin
api.prune(mstore, tenant="t")

api.pin(mstore, item, pinned=False)
api.prune(mstore, tenant="t")  # item removed
```

### Archiving

```python
api.archive(mstore, item_id, tenant="t", workspace="w")
```

Archived items are uploaded using the Discord CDN archiver and flagged in the
store so subsequent prune operations skip them.
