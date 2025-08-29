from __future__ import annotations

"""Render knowledge graph subgraphs to simple DOT graphs."""

from collections.abc import Iterable

from .store import KGEdge, KGNode


def render(nodes: Iterable[KGNode], edges: Iterable[KGEdge]) -> bytes:
    lines = ["digraph G {"]
    for n in nodes:
        lines.append(f'  {n.id} [label="{n.name}"]')
    for e in edges:
        lines.append(f'  {e.src_id} -> {e.dst_id} [label="{e.type}"]')
    lines.append("}")
    return "\n".join(lines).encode()
