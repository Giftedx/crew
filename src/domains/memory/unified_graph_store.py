"""Unified graph storage layer supporting multiple backends.

Provides a unified interface for graph operations across Neo4j (persistent,
production-ready queries), NetworkX (in-memory, fast testing), and Qdrant
(hybrid vector+graph retrieval via payload storage).
"""

from __future__ import annotations

import contextlib
import hashlib
import logging
from enum import Enum
from typing import TYPE_CHECKING, Any

from ultimate_discord_intelligence_bot.obs.metrics import get_metrics
from ultimate_discord_intelligence_bot.step_result import StepResult


if TYPE_CHECKING:
    from collections.abc import Sequence
logger = logging.getLogger(__name__)


class GraphBackend(str, Enum):
    """Supported graph storage backends."""

    NEO4J = "neo4j"
    NETWORKX = "networkx"
    QDRANT = "qdrant"


class UnifiedGraphStore:
    """Multi-backend graph storage with automatic routing.

    Provides consistent API for graph operations while allowing backend selection
    based on use case: Neo4j for production persistence, NetworkX for fast
    in-memory operations, Qdrant for hybrid vector+graph retrieval.
    """

    def __init__(
        self,
        *,
        default_backend: GraphBackend | str | None = None,
        neo4j_uri: str | None = None,
        neo4j_user: str | None = None,
        neo4j_password: str | None = None,
        qdrant_client: Any = None,
        enable_multi_backend: bool = True,
    ):
        """Initialize unified graph store.

        Args:
            default_backend: Default backend to use (neo4j, networkx, qdrant).
            neo4j_uri: Neo4j connection URI (e.g., bolt://localhost:7687).
            neo4j_user: Neo4j username.
            neo4j_password: Neo4j password.
            qdrant_client: Existing Qdrant client instance (optional).
            enable_multi_backend: If True, syncs writes across all backends.
        """
        from platform.config.configuration import get_config

        config = get_config()
        if default_backend is None:
            default_backend = getattr(config, "graph_backend", "neo4j")
        if isinstance(default_backend, str):
            default_backend = GraphBackend(default_backend.lower())
        self.default_backend = default_backend
        self.enable_multi_backend = enable_multi_backend
        self._metrics = get_metrics()
        self._neo4j_driver: Any = None
        self._networkx_graphs: dict[str, Any] = {}
        self._qdrant_client = qdrant_client
        if default_backend == GraphBackend.NEO4J or enable_multi_backend:
            try:
                from neo4j import GraphDatabase

                uri = neo4j_uri or getattr(config, "neo4j_uri", "bolt://neo4j:7687")
                user = neo4j_user or getattr(config, "neo4j_user", "neo4j")
                password = neo4j_password or getattr(config, "neo4j_password", "neo4j")
                self._neo4j_driver = GraphDatabase.driver(uri, auth=(user, password))
                logger.info(f"Connected to Neo4j at {uri}")
            except Exception as e:
                logger.warning(f"Failed to initialize Neo4j: {e}")
                if default_backend == GraphBackend.NEO4J:
                    logger.warning("Falling back to NetworkX backend")
                    self.default_backend = GraphBackend.NETWORKX
        if (default_backend == GraphBackend.QDRANT or enable_multi_backend) and self._qdrant_client is None:
            try:
                from domains.memory.vector.client_factory import get_qdrant_client

                self._qdrant_client = get_qdrant_client()
            except Exception as e:
                logger.warning(f"Failed to initialize Qdrant client: {e}")

    def add_node(
        self,
        node_id: str,
        *,
        labels: Sequence[str] | None = None,
        properties: dict[str, Any] | None = None,
        vector: list[float] | None = None,
        namespace: str = "default",
        backend: GraphBackend | str | None = None,
    ) -> StepResult:
        """Add a node to the graph.

        Args:
            node_id: Unique node identifier.
            labels: Node labels/types (e.g., ["Person", "Agent"]).
            properties: Node properties/attributes.
            vector: Embedding vector for the node (optional).
            namespace: Logical namespace for multi-tenancy.
            backend: Override default backend for this operation.

        Returns:
            StepResult with success status and backend used.
        """
        backend = self._resolve_backend(backend)
        labels = list(labels or [])
        properties = properties or {}
        try:
            if backend == GraphBackend.NEO4J:
                return self._neo4j_add_node(node_id, labels, properties, vector, namespace)
            elif backend == GraphBackend.NETWORKX:
                return self._nx_add_node(node_id, labels, properties, vector, namespace)
            elif backend == GraphBackend.QDRANT:
                return self._qdrant_add_node(node_id, labels, properties, vector, namespace)
            else:
                return StepResult.fail(f"Unsupported backend: {backend}")
        except Exception as exc:
            logger.exception(f"Failed to add node {node_id} to {backend}")
            return StepResult.fail(str(exc), node_id=node_id, backend=str(backend))

    def add_edge(
        self,
        source_id: str,
        target_id: str,
        *,
        relation: str,
        properties: dict[str, Any] | None = None,
        namespace: str = "default",
        backend: GraphBackend | str | None = None,
    ) -> StepResult:
        """Add an edge (relationship) between two nodes.

        Args:
            source_id: Source node ID.
            target_id: Target node ID.
            relation: Relationship type (e.g., "MENTIONS", "RELATES_TO").
            properties: Edge properties/attributes.
            namespace: Logical namespace for multi-tenancy.
            backend: Override default backend for this operation.

        Returns:
            StepResult with success status and backend used.
        """
        backend = self._resolve_backend(backend)
        properties = properties or {}
        try:
            if backend == GraphBackend.NEO4J:
                return self._neo4j_add_edge(source_id, target_id, relation, properties, namespace)
            elif backend == GraphBackend.NETWORKX:
                return self._nx_add_edge(source_id, target_id, relation, properties, namespace)
            elif backend == GraphBackend.QDRANT:
                return self._qdrant_add_edge(source_id, target_id, relation, properties, namespace)
            else:
                return StepResult.fail(f"Unsupported backend: {backend}")
        except Exception as exc:
            logger.exception(f"Failed to add edge {source_id}->{target_id} to {backend}")
            return StepResult.fail(str(exc), source_id=source_id, target_id=target_id, backend=str(backend))

    def query_subgraph(
        self,
        *,
        start_node: str,
        max_depth: int = 3,
        relation_filter: list[str] | None = None,
        namespace: str = "default",
        backend: GraphBackend | str | None = None,
    ) -> StepResult:
        """Query a subgraph starting from a node using BFS.

        Args:
            start_node: Starting node ID for traversal.
            max_depth: Maximum depth to traverse.
            relation_filter: Only follow edges with these relation types.
            namespace: Logical namespace for multi-tenancy.
            backend: Override default backend for this operation.

        Returns:
            StepResult with nodes, edges, and paths.
        """
        backend = self._resolve_backend(backend)
        try:
            if backend == GraphBackend.NEO4J:
                return self._neo4j_query_subgraph(start_node, max_depth, relation_filter, namespace)
            elif backend == GraphBackend.NETWORKX:
                return self._nx_query_subgraph(start_node, max_depth, relation_filter, namespace)
            elif backend == GraphBackend.QDRANT:
                return self._qdrant_query_subgraph(start_node, max_depth, relation_filter, namespace)
            else:
                return StepResult.fail(f"Unsupported backend: {backend}")
        except Exception as exc:
            logger.exception(f"Failed to query subgraph from {start_node} in {backend}")
            return StepResult.fail(str(exc), start_node=start_node, backend=str(backend))

    def _resolve_backend(self, backend: GraphBackend | str | None) -> GraphBackend:
        """Resolve backend to use for this operation."""
        if backend is None:
            return self.default_backend
        if isinstance(backend, str):
            return GraphBackend(backend.lower())
        return backend

    def _get_nx_graph(self, namespace: str) -> Any:
        """Get or create NetworkX graph for namespace."""
        if namespace not in self._networkx_graphs:
            try:
                import importlib

                nx_mod = importlib.import_module("networkx")
                self._networkx_graphs[namespace] = nx_mod.DiGraph()
            except ImportError:
                raise RuntimeError("NetworkX not available - install with: pip install networkx") from None
        return self._networkx_graphs[namespace]

    def _neo4j_add_node(
        self,
        node_id: str,
        labels: list[str],
        properties: dict[str, Any],
        vector: list[float] | None,
        namespace: str,
    ) -> StepResult:
        """Add node to Neo4j.

        Note: Vector embeddings are currently stored as properties ('embedding') in Neo4j,
        as native vector indexing requires specific index configuration not yet implemented.
        """
        if self._neo4j_driver is None:
            return StepResult.fail("Neo4j driver not initialized")

        props = properties.copy()
        if vector is not None:
            props["embedding"] = vector

        props["_namespace"] = namespace
        props["_node_id"] = node_id
        label_str = ":".join(labels) if labels else "Node"
        cypher = f"MERGE (n:{label_str} {{_node_id: $node_id, _namespace: $namespace}}) SET n += $props RETURN n"
        with self._neo4j_driver.session() as session:
            result = session.run(cypher, node_id=node_id, namespace=namespace, props=props)
            _ = result.single()
        self._metrics.counter(
            "graph_store_operations_total", labels={"backend": "neo4j", "operation": "add_node"}
        ).inc()
        return StepResult.ok(node_id=node_id, backend="neo4j", namespace=namespace)

    def _neo4j_add_edge(
        self, source_id: str, target_id: str, relation: str, properties: dict[str, Any], namespace: str
    ) -> StepResult:
        """Add edge to Neo4j."""
        if self._neo4j_driver is None:
            return StepResult.fail("Neo4j driver not initialized")
        properties["_namespace"] = namespace
        cypher = f"\n        MATCH (a {{_node_id: $source_id, _namespace: $namespace}})\n        MATCH (b {{_node_id: $target_id, _namespace: $namespace}})\n        MERGE (a)-[r:{relation}]->(b)\n        SET r += $props\n        RETURN r\n        "
        with self._neo4j_driver.session() as session:
            result = session.run(
                cypher, source_id=source_id, target_id=target_id, namespace=namespace, props=properties
            )
            _ = result.single()
        self._metrics.counter(
            "graph_store_operations_total", labels={"backend": "neo4j", "operation": "add_edge"}
        ).inc()
        return StepResult.ok(source_id=source_id, target_id=target_id, relation=relation, backend="neo4j")

    def _neo4j_query_subgraph(
        self, start_node: str, max_depth: int, relation_filter: list[str] | None, namespace: str
    ) -> StepResult:
        """Query subgraph from Neo4j using Cypher path queries."""
        if self._neo4j_driver is None:
            return StepResult.fail("Neo4j driver not initialized")
        rel_filter = "|".join(relation_filter) if relation_filter else ""
        rel_pattern = f"[r:{rel_filter}]" if rel_filter else "[r]"
        cypher = f"\n        MATCH path = (start {{_node_id: $start_node, _namespace: $namespace}})\n                     -{rel_pattern}*1..{max_depth}->\n                     (end)\n        WHERE start._namespace = $namespace AND end._namespace = $namespace\n        RETURN nodes(path) as nodes, relationships(path) as edges\n        "
        with self._neo4j_driver.session() as session:
            result = session.run(cypher, start_node=start_node, namespace=namespace)
            all_nodes: dict[str, dict] = {}
            all_edges: list[dict] = []
            for record in result:
                for node in record["nodes"]:
                    node_dict = dict(node)
                    all_nodes[node_dict["_node_id"]] = node_dict
                for edge in record["edges"]:
                    edge_dict = dict(edge)
                    all_edges.append(edge_dict)
        self._metrics.counter("graph_store_operations_total", labels={"backend": "neo4j", "operation": "query"}).inc()
        return StepResult.ok(
            nodes=list(all_nodes.values()),
            edges=all_edges,
            node_count=len(all_nodes),
            edge_count=len(all_edges),
            backend="neo4j",
        )

    def _nx_add_node(
        self,
        node_id: str,
        labels: list[str],
        properties: dict[str, Any],
        vector: list[float] | None,
        namespace: str,
    ) -> StepResult:
        """Add node to NetworkX graph."""
        graph = self._get_nx_graph(namespace)
        props = properties.copy()
        if vector is not None:
            props["_vector"] = vector
        graph.add_node(node_id, labels=labels, **props)
        self._metrics.counter(
            "graph_store_operations_total", labels={"backend": "networkx", "operation": "add_node"}
        ).inc()
        return StepResult.ok(node_id=node_id, backend="networkx", namespace=namespace)

    def _nx_add_edge(
        self, source_id: str, target_id: str, relation: str, properties: dict[str, Any], namespace: str
    ) -> StepResult:
        """Add edge to NetworkX graph."""
        graph = self._get_nx_graph(namespace)
        if source_id not in graph:
            graph.add_node(source_id)
        if target_id not in graph:
            graph.add_node(target_id)
        graph.add_edge(source_id, target_id, relation=relation, **properties)
        self._metrics.counter(
            "graph_store_operations_total", labels={"backend": "networkx", "operation": "add_edge"}
        ).inc()
        return StepResult.ok(source_id=source_id, target_id=target_id, relation=relation, backend="networkx")

    def _nx_query_subgraph(
        self, start_node: str, max_depth: int, relation_filter: list[str] | None, namespace: str
    ) -> StepResult:
        """Query subgraph from NetworkX using BFS."""
        graph = self._get_nx_graph(namespace)
        if start_node not in graph:
            return StepResult.fail(f"Start node {start_node} not found in graph", start_node=start_node)
        from collections import deque

        visited: set[str] = {start_node}
        queue: deque[tuple[str, int]] = deque([(start_node, 0)])
        while queue:
            current, depth = queue.popleft()
            if depth >= max_depth:
                continue
            for neighbor in graph.successors(current):
                edge_data = graph.edges[current, neighbor]
                if relation_filter:
                    rel = edge_data.get("relation")
                    if rel not in relation_filter:
                        continue
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append((neighbor, depth + 1))
        subgraph = graph.subgraph(visited).copy()
        nodes = [{"id": n, **(subgraph.nodes[n] or {})} for n in subgraph.nodes]
        edges = [{"source": s, "target": t, **(subgraph.edges[s, t] or {})} for s, t in subgraph.edges]
        self._metrics.counter(
            "graph_store_operations_total", labels={"backend": "networkx", "operation": "query"}
        ).inc()
        return StepResult.ok(nodes=nodes, edges=edges, node_count=len(nodes), edge_count=len(edges), backend="networkx")

    def _qdrant_add_node(
        self,
        node_id: str,
        labels: list[str],
        properties: dict[str, Any],
        vector: list[float] | None,
        namespace: str,
    ) -> StepResult:
        """Add node to Qdrant as a point with graph metadata in payload."""
        if self._qdrant_client is None:
            return StepResult.fail("Qdrant client not initialized")
        payload = {"_graph_type": "node", "_node_id": node_id, "_namespace": namespace, "_labels": labels, **properties}
        from qdrant_client.models import PointStruct

        vec_data = vector if vector is not None else [0.0] * 384
        # Use SHA256 for deterministic ID generation instead of unstable hash()
        id_hash = hashlib.sha256(f"{namespace}:{node_id}".encode("utf-8")).hexdigest()
        # Qdrant supports UUID strings or uint64 integers. We use the first 64 bits of the hash.
        # Actually, python's int from hex is easiest, but Qdrant often prefers UUIDs.
        # For simplicity and backward compat with the hash() approach (which yielded ints),
        # we'll generate a UUID-like string or a large int.
        # The previous code used a 31-bit int: hash(...) & 2147483647.
        # Let's use a full UUID for better uniqueness.
        import uuid
        point_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"{namespace}:{node_id}"))

        point = PointStruct(id=point_id, vector=vec_data, payload=payload)
        collection_name = f"graph_memory_{namespace}"
        with contextlib.suppress(Exception):
            from qdrant_client.models import Distance, VectorParams

            self._qdrant_client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(size=len(vec_data), distance=Distance.COSINE),
            )
        self._qdrant_client.upsert(collection_name=collection_name, points=[point])
        self._metrics.counter(
            "graph_store_operations_total", labels={"backend": "qdrant", "operation": "add_node"}
        ).inc()
        return StepResult.ok(node_id=node_id, backend="qdrant", namespace=namespace)

    def _qdrant_add_edge(
        self, source_id: str, target_id: str, relation: str, properties: dict[str, Any], namespace: str
    ) -> StepResult:
        """Add edge to Qdrant by updating source node's payload."""
        if self._qdrant_client is None:
            return StepResult.fail("Qdrant client not initialized")
        collection_name = f"graph_memory_{namespace}"
        from qdrant_client.models import FieldCondition, Filter, MatchValue

        search_result = self._qdrant_client.scroll(
            collection_name=collection_name,
            scroll_filter=Filter(must=[FieldCondition(key="_node_id", match=MatchValue(value=source_id))]),
            limit=1,
        )
        if not search_result[0]:
            return StepResult.fail(f"Source node {source_id} not found")
        point = search_result[0][0]
        payload = dict(point.payload)
        if "_edges" not in payload:
            payload["_edges"] = []
        payload["_edges"].append({"target": target_id, "relation": relation, **properties})
        from qdrant_client.models import PointStruct

        updated_point = PointStruct(id=point.id, vector=point.vector, payload=payload)
        self._qdrant_client.upsert(collection_name=collection_name, points=[updated_point])
        self._metrics.counter(
            "graph_store_operations_total", labels={"backend": "qdrant", "operation": "add_edge"}
        ).inc()
        return StepResult.ok(source_id=source_id, target_id=target_id, relation=relation, backend="qdrant")

    def _qdrant_query_subgraph(
        self, start_node: str, max_depth: int, relation_filter: list[str] | None, namespace: str
    ) -> StepResult:
        """Query subgraph from Qdrant by traversing edge payloads."""
        if self._qdrant_client is None:
            return StepResult.fail("Qdrant client not initialized")
        collection_name = f"graph_memory_{namespace}"
        from collections import deque

        from qdrant_client.models import FieldCondition, Filter, MatchValue

        visited: set[str] = {start_node}
        queue: deque[tuple[str, int]] = deque([(start_node, 0)])
        all_nodes: list[dict] = []
        all_edges: list[dict] = []
        while queue:
            current_id, depth = queue.popleft()
            if depth >= max_depth:
                continue
            result = self._qdrant_client.scroll(
                collection_name=collection_name,
                scroll_filter=Filter(must=[FieldCondition(key="_node_id", match=MatchValue(value=current_id))]),
                limit=1,
            )
            if not result[0]:
                continue
            point = result[0][0]
            payload = point.payload
            all_nodes.append(dict(payload))
            for edge in payload.get("_edges", []):
                target_id = edge["target"]
                relation = edge.get("relation")
                if relation_filter and relation not in relation_filter:
                    continue
                all_edges.append({"source": current_id, "target": target_id, "relation": relation})
                if target_id not in visited:
                    visited.add(target_id)
                    queue.append((target_id, depth + 1))
        self._metrics.counter("graph_store_operations_total", labels={"backend": "qdrant", "operation": "query"}).inc()
        return StepResult.ok(
            nodes=all_nodes, edges=all_edges, node_count=len(all_nodes), edge_count=len(all_edges), backend="qdrant"
        )

    def close(self) -> None:
        """Close all backend connections."""
        if self._neo4j_driver is not None:
            with contextlib.suppress(Exception):
                self._neo4j_driver.close()
                logger.info("Closed Neo4j driver")


__all__ = ["GraphBackend", "UnifiedGraphStore"]
