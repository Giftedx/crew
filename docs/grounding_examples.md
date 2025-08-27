# Grounding Examples

```python
from grounding import contracts, retriever, verifier
from grounding.schema import Evidence
from memory import api as memory_api, MemoryStore
import memory.vector_store as vector_store

mstore = MemoryStore(":memory:")
vstore = vector_store.VectorStore()
memory_api.store(mstore, vstore, tenant="t", workspace="w", text="cats purr")
pack = retriever.gather(mstore, vstore, tenant="t", workspace="w", query="cats")
contract = contracts.build_contract("Cats purr [1]", pack.snippets, use_case="context")
report = verifier.verify(contract, use_case="context")
assert report.verdict == "pass"
```
