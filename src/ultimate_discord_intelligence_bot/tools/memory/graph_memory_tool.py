from __future__ import annotations

import contextlib
import json
import os
import re
from collections import Counter
from pathlib import Path
from typing import TYPE_CHECKING, Any
from uuid import uuid4

from ultimate_discord_intelligence_bot.obs.metrics import get_metrics
from ultimate_discord_intelligence_bot.step_result import StepResult

from ._base import BaseTool


if TYPE_CHECKING:
    from collections.abc import Iterable


try:  # pragma: no cover - optional heavy dependency
    import networkx as nx
except Exception:  # pragma: no cover
    nx = None  # type: ignore


def _normalise_metadata(metadata: dict[str, Any] | None) -> dict[str, Any]:
    if not isinstance(metadata, dict):
        return {}
    normalised: dict[str, Any] = {}
    for key, value in metadata.items():
        if isinstance(value, (str, int, float, bool)) or value is None:
            normalised[key] = value
        else:
            normalised[key] = repr(value)
    return normalised


def _split_sentences(text: str) -> list[str]:
    sentences = [segment.strip() for segment in re.split(r"(?<=[.!?])\s+", text) if segment.strip()]
    if not sentences and text.strip():
        sentences = [text.strip()]
    return sentences


def _extract_keywords(text: str, *, limit: int = 12) -> list[str]:
    tokens = re.findall(r"[A-Za-z][A-Za-z0-9_-]{2,}", text)
    if not tokens:
        return []
    counts = Counter(token.lower() for token in tokens)
    return [token for token, _ in counts.most_common(limit)]


def _build_graph(text: str) -> dict[str, Any]:
    sentences = _split_sentences(text)
    keywords = _extract_keywords(text)
    if nx is None:
        nodes: list[dict[str, Any]] = []
        edges: list[dict[str, Any]] = []
        for idx, sentence in enumerate(sentences):
            node_id = f"sentence_{idx + 1}"
            nodes.append({"id": node_id, "label": sentence})
            if idx > 0:
                edges.append(
                    {
                        "source": f"sentence_{idx}",
                        "target": node_id,
                        "relation": "sequence",
                    }
                )
        for kw in keywords:
            kw_id = f"keyword_{kw}"
            nodes.append({"id": kw_id, "label": kw, "type": "keyword"})
            if sentences:
                edges.append(
                    {
                        "source": kw_id,
                        "target": "sentence_1",
                        "relation": "mentions",
                    }
                )
        return {"nodes": nodes, "edges": edges, "keywords": keywords}

    graph = nx.DiGraph()
    for idx, sentence in enumerate(sentences):
        node_id = f"sentence_{idx + 1}"
        graph.add_node(node_id, label=sentence, type="sentence", order=idx + 1)
        if idx > 0:
            graph.add_edge(f"sentence_{idx}", node_id, relation="sequence")
    for kw in keywords:
        kw_id = f"keyword_{kw}"
        graph.add_node(kw_id, label=kw, type="keyword")
        for idx, sentence in enumerate(sentences[:3]):
            graph.add_edge(kw_id, f"sentence_{idx + 1}", relation="mentions")
    return {
        "nodes": [{"id": node, **(graph.nodes[node] or {})} for node in graph.nodes],
        "edges": [{"source": src, "target": dst, **(graph.edges[src, dst] or {})} for src, dst in graph.edges],
        "keywords": keywords,
    }


class GraphMemoryTool(BaseTool[StepResult]):
    """Persist lightweight knowledge graph structures for later retrieval.

    The tool accepts pre-filtered text (e.g. analysis summaries) and constructs
    a tenant-scoped graph capturing coarse relationships between sentences and
    extracted keywords. When Microsoft GraphRAG is available in the runtime it
    can be substituted by overriding the graph builder; the default
    implementation relies on ``networkx`` with a deterministic heuristic graph
    layout to remain lightweight and dependency-free during tests.
    """

    name: str = "Graph Memory Tool"
    description: str = "Store heuristic knowledge graphs derived from text in a tenant-scoped namespace."

    def __init__(self, storage_dir: str | os.PathLike[str] | None = None) -> None:
        super().__init__()
        base_dir = storage_dir or os.getenv("GRAPH_MEMORY_STORAGE", "crew_data/Processing/graph_memory")
        self._base_path = Path(base_dir)
        self._base_path.mkdir(parents=True, exist_ok=True)
        self._metrics = get_metrics()

    @staticmethod
    def _physical_namespace(namespace: str) -> str:
        safe = namespace.replace(":", "__").replace("/", "_")
        return re.sub(r"[^A-Za-z0-9_.-]", "_", safe)

    def _namespace_path(self, namespace: str) -> Path:
        physical = self._physical_namespace(namespace)
        path = self._base_path / physical
        path.mkdir(parents=True, exist_ok=True)
        return path

    def _resolve_namespace(self, index: str) -> tuple[str, bool]:
        try:
            from ultimate_discord_intelligence_bot.tenancy.context import (
                current_tenant,
                mem_ns,
            )  # type: ignore

            ctx = current_tenant()
            if ctx is not None:
                return mem_ns(ctx, index), True
        except Exception:
            pass
        return index, False

    def run(
        self,
        *,
        text: str,
        index: str = "graph",
        metadata: dict[str, Any] | None = None,
        tags: Iterable[str] | None = None,
    ) -> StepResult:
        if not isinstance(text, str) or not text.strip():
            with contextlib.suppress(Exception):
                self._metrics.counter(
                    "tool_runs_total",
                    labels={"tool": "graph_memory", "outcome": "skipped"},
                ).inc()
            return StepResult.skip(reason="empty_text")

        namespace, tenant_scoped = self._resolve_namespace(index)
        try:
            graph_payload = _build_graph(text)
            graph_id = uuid4().hex
            keywords = graph_payload.get("keywords") or []
            graph_payload["keywords"] = keywords
            graph_payload["metadata"] = {
                "tenant_scoped": tenant_scoped,
                "namespace": namespace,
                "keywords": keywords,
                "tags": list(tags or []),
                "source_metadata": _normalise_metadata(metadata),
            }
            graph_payload.setdefault("nodes", [])
            graph_payload.setdefault("edges", [])
            graph_payload["metadata"]["node_count"] = len(graph_payload["nodes"])
            graph_payload["metadata"]["edge_count"] = len(graph_payload["edges"])

            ns_path = self._namespace_path(namespace)
            file_path = ns_path / f"{graph_id}.json"
            with file_path.open("w", encoding="utf-8") as handle:
                json.dump(graph_payload, handle, ensure_ascii=False, indent=2)

            with contextlib.suppress(Exception):
                self._metrics.counter(
                    "tool_runs_total",
                    labels={
                        "tool": "graph_memory",
                        "outcome": "success",
                        "tenant_scoped": str(tenant_scoped).lower(),
                    },
                ).inc()

            return StepResult.ok(
                graph_id=graph_id,
                namespace=namespace,
                tenant_scoped=tenant_scoped,
                storage_path=str(file_path),
                node_count=len(graph_payload["nodes"]),
                edge_count=len(graph_payload["edges"]),
                keywords=graph_payload["metadata"].get("keywords", []),
            )
        except Exception as exc:  # pragma: no cover - defensive path
            with contextlib.suppress(Exception):
                self._metrics.counter(
                    "tool_runs_total",
                    labels={
                        "tool": "graph_memory",
                        "outcome": "error",
                        "tenant_scoped": str(tenant_scoped).lower(),
                    },
                ).inc()
            return StepResult.fail(str(exc), namespace=namespace)

    def list_graphs(self, *, namespace: str = "graph") -> StepResult:
        """List all graph IDs in a namespace.

        Args:
            namespace: Logical namespace (will be tenant-scoped if context available).

        Returns:
            StepResult with graph_ids list, count, and resolved namespace.
        """
        namespace, tenant_scoped = self._resolve_namespace(namespace)
        ns_path = self._namespace_path(namespace)

        if not ns_path.exists():
            return StepResult.ok(graph_ids=[], count=0, namespace=namespace, tenant_scoped=tenant_scoped)

        graph_ids = [f.stem for f in ns_path.glob("*.json")]

        with contextlib.suppress(Exception):
            self._metrics.counter(
                "graph_memory_lists_total",
                labels={
                    "namespace": namespace,
                    "tenant_scoped": str(tenant_scoped).lower(),
                },
            ).inc()

        return StepResult.ok(
            graph_ids=graph_ids,
            count=len(graph_ids),
            namespace=namespace,
            tenant_scoped=tenant_scoped,
        )

    def search_graphs(
        self,
        *,
        query: str | None = None,
        namespace: str = "graph",
        tags: list[str] | None = None,
        limit: int = 10,
    ) -> StepResult:
        """Search for graphs matching query/tags.

        Args:
            query: Text query to match against keywords, node labels.
            namespace: Logical namespace (will be tenant-scoped if context available).
            tags: Filter by specific tags (must match at least one).
            limit: Maximum number of results to return.

        Returns:
            StepResult with list of matching graphs (metadata), count, and namespace.
        """
        namespace, tenant_scoped = self._resolve_namespace(namespace)
        ns_path = self._namespace_path(namespace)

        if not ns_path.exists() or not any(ns_path.glob("*.json")):
            return StepResult.ok(graphs=[], count=0, namespace=namespace, tenant_scoped=tenant_scoped)

        matches: list[dict[str, Any]] = []
        query_keywords = set(_extract_keywords(query)) if query else set()

        for json_file in ns_path.glob("*.json"):
            try:
                with json_file.open("r", encoding="utf-8") as f:
                    graph_data = json.load(f)

                metadata = graph_data.get("metadata", {})

                # Tag filter (exact match required if specified)
                if tags:
                    graph_tags = set(metadata.get("tags", []))
                    if not graph_tags.intersection(tags):
                        continue

                # Keyword scoring
                score = 0.0
                if query_keywords:
                    graph_keywords = set(metadata.get("keywords", []))
                    overlap = query_keywords.intersection(graph_keywords)
                    score = len(overlap) / len(query_keywords) if query_keywords else 0.0
                else:
                    score = 1.0  # No query = all graphs match equally

                matches.append(
                    {
                        "graph_id": json_file.stem,
                        "score": score,
                        "keywords": metadata.get("keywords", []),
                        "tags": metadata.get("tags", []),
                        "node_count": metadata.get("node_count", 0),
                        "edge_count": metadata.get("edge_count", 0),
                        "tenant_scoped": metadata.get("tenant_scoped", False),
                    }
                )
            except Exception:
                continue  # Skip corrupted files

        # Sort by score (descending) and limit
        matches.sort(key=lambda x: x["score"], reverse=True)
        results = matches[:limit]

        with contextlib.suppress(Exception):
            self._metrics.counter(
                "graph_memory_searches_total",
                labels={
                    "namespace": namespace,
                    "tenant_scoped": str(tenant_scoped).lower(),
                },
            ).inc()

        return StepResult.ok(
            graphs=results,
            count=len(results),
            namespace=namespace,
            tenant_scoped=tenant_scoped,
        )

    def get_graph(self, *, graph_id: str, namespace: str = "graph") -> StepResult:
        """Retrieve a specific graph by ID.

        Args:
            graph_id: UUID hex string of the graph to retrieve.
            namespace: Logical namespace (will be tenant-scoped if context available).

        Returns:
            StepResult with full graph structure (nodes, edges, keywords, metadata).
        """
        namespace, tenant_scoped = self._resolve_namespace(namespace)
        ns_path = self._namespace_path(namespace)

        file_path = ns_path / f"{graph_id}.json"
        if not file_path.exists():
            return StepResult.fail(
                f"Graph not found: {graph_id}",
                namespace=namespace,
                graph_id=graph_id,
            )

        try:
            with file_path.open("r", encoding="utf-8") as f:
                graph_data = json.load(f)

            with contextlib.suppress(Exception):
                self._metrics.counter(
                    "graph_memory_retrievals_total",
                    labels={
                        "namespace": namespace,
                        "tenant_scoped": str(tenant_scoped).lower(),
                    },
                ).inc()

            return StepResult.ok(
                graph_id=graph_id,
                nodes=graph_data.get("nodes", []),
                edges=graph_data.get("edges", []),
                keywords=graph_data.get("keywords", []),
                metadata=graph_data.get("metadata", {}),
                namespace=namespace,
                tenant_scoped=tenant_scoped,
            )
        except Exception as exc:
            return StepResult.fail(
                f"Failed to load graph: {exc}",
                namespace=namespace,
                graph_id=graph_id,
            )

    def traverse_graph(
        self,
        *,
        graph_id: str,
        start_node: str,
        max_depth: int = 3,
        relation_filter: list[str] | None = None,
        namespace: str = "graph",
    ) -> StepResult:
        """Traverse graph from a starting node using BFS.

        Args:
            graph_id: UUID hex string of the graph.
            start_node: Node ID to start from (e.g., "keyword_AI", "sentence_1").
            max_depth: Maximum number of edge hops from start node.
            relation_filter: Only follow edges with these relation types.
            namespace: Logical namespace (will be tenant-scoped if context available).

        Returns:
            StepResult with visited_nodes, paths, and extracted subgraph.
        """
        # First retrieve the graph
        graph_result = self.get_graph(graph_id=graph_id, namespace=namespace)
        if not graph_result.success:
            return graph_result

        nodes = graph_result.data["nodes"]
        edges = graph_result.data["edges"]

        # Build adjacency list
        adjacency: dict[str, list[dict[str, Any]]] = {}
        for edge in edges:
            src = edge.get("source")
            dst = edge.get("target")
            rel = edge.get("relation")

            # Apply relation filter
            if relation_filter and rel not in relation_filter:
                continue

            if src not in adjacency:
                adjacency[src] = []
            adjacency[src].append({"target": dst, "relation": rel})

        # BFS traversal
        from collections import deque

        visited: set[str] = {start_node}
        queue: deque[tuple[str, int, list[str]]] = deque([(start_node, 0, [start_node])])
        paths: dict[str, list[str]] = {start_node: [start_node]}

        while queue:
            current, depth, path = queue.popleft()

            if depth >= max_depth:
                continue

            for neighbor_info in adjacency.get(current, []):
                neighbor = neighbor_info["target"]

                if neighbor not in visited:
                    visited.add(neighbor)
                    new_path = [*path, neighbor]
                    paths[neighbor] = new_path
                    queue.append((neighbor, depth + 1, new_path))

        # Extract subgraph
        visited_nodes = [n for n in nodes if n.get("id") in visited]
        visited_edges = [e for e in edges if e.get("source") in visited and e.get("target") in visited]

        with contextlib.suppress(Exception):
            self._metrics.counter(
                "graph_memory_traversals_total",
                labels={"namespace": graph_result.data["namespace"]},
            ).inc()

        return StepResult.ok(
            graph_id=graph_id,
            start_node=start_node,
            visited_nodes=visited_nodes,
            paths=paths,
            subgraph={"nodes": visited_nodes, "edges": visited_edges},
            node_count=len(visited_nodes),
            edge_count=len(visited_edges),
            max_depth=max_depth,
            namespace=graph_result.data["namespace"],
            tenant_scoped=graph_result.data.get("tenant_scoped", False),
        )


__all__ = ["GraphMemoryTool"]
