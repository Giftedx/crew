# Knowledge Graph Examples

```python
from kg import KGStore, timeline

store = KGStore()
entity = store.add_node("tenant", "entity", "Alice")
episode = store.add_node("tenant", "episode", "Debate")
store.add_edge(entity, episode, "mentions", created_at="1")

for event in timeline(store, "Alice", "tenant"):
    print(event)
```

The snippet above yields a single `TimelineEvent` linking *Alice* to *Debate*.
