"""Render knowledge graph subgraphs to simple DOT graphs."""

from __future__ import annotations

from collections.abc import Iterable

from .store import KGEdge, KGNode


def render(nodes: Iterable[KGNode], edges: Iterable[KGEdge]) -> bytes:
    lines = ["digraph G {"]
    lines.extend(f'  {n.id} [label="{n.name}"]' for n in nodes)
    lines.extend(f'  {e.src_id} -> {e.dst_id} [label="{e.type}"]' for e in edges)
    lines.append("}")
    return "\n".join(lines).encode()
