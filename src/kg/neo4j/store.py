"""Neo4j-backed knowledge graph store.

Provides enhanced graph database capabilities with Cypher query support,
relationship analysis, and scalable multi-tenant graph operations.
"""

from __future__ import annotations

import json
import logging
from typing import TYPE_CHECKING, Any


try:
    from neo4j import Driver, GraphDatabase
    NEO4J_AVAILABLE = True
except ImportError:
    NEO4J_AVAILABLE = False
    Driver = None  # type: ignore[assignment,misc]

if TYPE_CHECKING:
    from collections.abc import Iterable

from src.kg.store import KGEdge, KGNode


_logger = logging.getLogger(__name__)


class Neo4jKGStore:
    """Neo4j-backed knowledge graph store with Cypher support."""

    def __init__(
        self,
        uri: str = "bolt://localhost:7687",
        user: str = "neo4j",
        password: str = "password",
    ):
        if not NEO4J_AVAILABLE:
            raise ImportError("Neo4j driver not available. Install with: pip install neo4j")

        self.driver: Driver = GraphDatabase.driver(uri, auth=(user, password))
        self._ensure_constraints()

    def close(self) -> None:
        """Close the Neo4j driver connection."""
        self.driver.close()

    def _ensure_constraints(self) -> None:
        """Create indexes and constraints for performance."""
        with self.driver.session() as session:
            # Create unique constraint on tenant + name
            session.run(
                """
                CREATE CONSTRAINT IF NOT EXISTS FOR (n:Node)
                REQUIRE (n.tenant, n.name) IS UNIQUE
                """
            )
            # Create index on tenant for faster queries
            session.run(
                """
                CREATE INDEX IF NOT EXISTS FOR (n:Node) ON (n.tenant)
                """
            )
            # Create index on type for faster filtering
            session.run(
                """
                CREATE INDEX IF NOT EXISTS FOR (n:Node) ON (n.type)
                """
            )

    def add_node(
        self,
        tenant: str,
        type: str,
        name: str,
        attrs: dict[str, Any] | None = None,
        created_at: str = "",
    ) -> int:
        """Add a node to the graph."""
        attrs_json = json.dumps(attrs or {})

        with self.driver.session() as session:
            result = session.run(
                """
                MERGE (n:Node {tenant: $tenant, name: $name})
                SET n.type = $type,
                    n.attrs_json = $attrs_json,
                    n.created_at = $created_at
                RETURN id(n) as node_id
                """,
                tenant=tenant,
                name=name,
                type=type,
                attrs_json=attrs_json,
                created_at=created_at,
            )
            record = result.single()
            return record["node_id"] if record else 0

    def query_nodes(
        self,
        tenant: str,
        *,
        type: str | None = None,
        name: str | None = None,
    ) -> list[KGNode]:
        """Query nodes matching criteria."""
        conditions = ["n.tenant = $tenant"]
        params: dict[str, Any] = {"tenant": tenant}

        if type:
            conditions.append("n.type = $type")
            params["type"] = type
        if name:
            conditions.append("n.name = $name")
            params["name"] = name

        query = f"""
        MATCH (n:Node)
        WHERE {' AND '.join(conditions)}
        RETURN id(n) as id, n.tenant as tenant, n.type as type,
               n.name as name, n.attrs_json as attrs_json, n.created_at as created_at
        """

        with self.driver.session() as session:
            result = session.run(query, **params)
            return [
                KGNode(
                    id=record["id"],
                    tenant=record["tenant"],
                    type=record["type"],
                    name=record["name"],
                    attrs_json=record["attrs_json"],
                    created_at=record["created_at"],
                )
                for record in result
            ]

    def get_node(self, node_id: int) -> KGNode | None:
        """Get a node by ID."""
        with self.driver.session() as session:
            result = session.run(
                """
                MATCH (n:Node)
                WHERE id(n) = $node_id
                RETURN id(n) as id, n.tenant as tenant, n.type as type,
                       n.name as name, n.attrs_json as attrs_json, n.created_at as created_at
                """,
                node_id=node_id,
            )
            record = result.single()
            if not record:
                return None

            return KGNode(
                id=record["id"],
                tenant=record["tenant"],
                type=record["type"],
                name=record["name"],
                attrs_json=record["attrs_json"],
                created_at=record["created_at"],
            )

    def add_edge(
        self,
        src_id: int,
        dst_id: int,
        type: str,
        *,
        weight: float = 1.0,
        provenance_id: int | None = None,
        created_at: str = "",
    ) -> int:
        """Add an edge (relationship) to the graph."""
        with self.driver.session() as session:
            result = session.run(
                """
                MATCH (src:Node), (dst:Node)
                WHERE id(src) = $src_id AND id(dst) = $dst_id
                CREATE (src)-[r:RELATES {type: $type, weight: $weight,
                                         provenance_id: $provenance_id,
                                         created_at: $created_at}]->(dst)
                RETURN id(r) as edge_id
                """,
                src_id=src_id,
                dst_id=dst_id,
                type=type,
                weight=weight,
                provenance_id=provenance_id,
                created_at=created_at,
            )
            record = result.single()
            return record["edge_id"] if record else 0

    def query_edges(
        self,
        *,
        src_id: int | None = None,
        dst_id: int | None = None,
        type: str | None = None,
    ) -> list[KGEdge]:
        """Query edges matching criteria."""
        query = "MATCH (src:Node)-[r:RELATES]->(dst:Node)"
        conditions: list[str] = []
        params: dict[str, Any] = {}

        if src_id is not None:
            conditions.append("id(src) = $src_id")
            params["src_id"] = src_id
        if dst_id is not None:
            conditions.append("id(dst) = $dst_id")
            params["dst_id"] = dst_id
        if type is not None:
            conditions.append("r.type = $type")
            params["type"] = type

        if conditions:
            query += " WHERE " + " AND ".join(conditions)

        query += """
        RETURN id(r) as id, id(src) as src_id, id(dst) as dst_id,
               r.type as type, r.weight as weight,
               r.provenance_id as provenance_id, r.created_at as created_at
        """

        with self.driver.session() as session:
            result = session.run(query, **params)
            return [
                KGEdge(
                    id=record["id"],
                    src_id=record["src_id"],
                    dst_id=record["dst_id"],
                    type=record["type"],
                    weight=record["weight"],
                    provenance_id=record["provenance_id"],
                    created_at=record["created_at"],
                )
                for record in result
            ]

    def neighbors(self, node_id: int, depth: int = 1) -> Iterable[int]:
        """Return node IDs reachable within depth hops."""
        # Validate depth to prevent injection (Cypher variable-length patterns cannot be parameterized)
        if not isinstance(depth, int) or depth < 1 or depth > 10:
            raise ValueError(f"Invalid depth: must be an integer between 1 and 10, got {depth}")

        with self.driver.session() as session:
            result = session.run(
                """
                MATCH path = (start:Node)-[*1..%d]->(neighbor:Node)
                WHERE id(start) = $node_id
                RETURN DISTINCT id(neighbor) as neighbor_id
                """ % depth,
                node_id=node_id,
            )
            return [record["neighbor_id"] for record in result]

    def cypher_query(self, query: str, **params: Any) -> list[dict[str, Any]]:
        """Execute a custom Cypher query."""
        with self.driver.session() as session:
            result = session.run(query, **params)
            return [dict(record) for record in result]

    def get_relationship_graph(self, node_id: int, max_depth: int = 2) -> dict[str, Any]:
        """Get a subgraph centered on a node for visualization."""
        # Validate max_depth to prevent injection (Cypher variable-length patterns cannot be parameterized)
        if not isinstance(max_depth, int) or max_depth < 1 or max_depth > 10:
            raise ValueError(f"Invalid max_depth: must be an integer between 1 and 10, got {max_depth}")

        with self.driver.session() as session:
            result = session.run(
                """
                MATCH path = (center:Node)-[*1..%d]-(connected:Node)
                WHERE id(center) = $node_id
                RETURN path, nodes(path) as nodes, relationships(path) as edges
                LIMIT 100
                """ % max_depth,
                node_id=node_id,
            )

            nodes = set()
            edges = []

            for record in result:
                for node in record["nodes"]:
                    nodes.add((id(node), node["name"], node["type"]))
                for edge in record["edges"]:
                    edges.append({
                        "src": edge.start_node["name"],
                        "dst": edge.end_node["name"],
                        "type": edge.get("type", "RELATES"),
                        "weight": edge.get("weight", 1.0),
                    })

            return {
                "nodes": [{"id": n[0], "name": n[1], "type": n[2]} for n in nodes],
                "edges": edges,
            }
