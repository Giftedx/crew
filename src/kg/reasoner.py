"""Simple reasoning utilities for the knowledge graph."""

from __future__ import annotations

from dataclasses import dataclass

from .store import KGStore


@dataclass
class TimelineEvent:
    node_id: int
    name: str
    timestamp: float


def timeline(store: KGStore, entity_name: str, tenant: str) -> list[TimelineEvent]:
    """Return events where the entity is mentioned ordered by ``created_at``."""
    nodes = store.query_nodes(tenant, type="entity", name=entity_name)
    if not nodes:
        return []
    entity_id = nodes[0].id
    edges = store.query_edges(src_id=entity_id, type="mentions")
    events: list[TimelineEvent] = []
    for edge in edges:
        target = store.get_node(edge.dst_id)
        if target is None:
            continue
        try:
            ts = float(edge.created_at)
        except ValueError:
            ts = 0.0
        events.append(TimelineEvent(node_id=target.id or 0, name=target.name, timestamp=ts))
    events.sort(key=lambda e: e.timestamp)
    return events
