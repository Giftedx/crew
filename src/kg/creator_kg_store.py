"""Extended KGStore with creator-focused schema and operations.

This module extends the base KGStore with creator-specific functionality,
including schema validation, specialized queries, and migration support.
"""

from __future__ import annotations

from typing import Any

from .creator_schema import (
    CREATOR_EDGE_TYPES,
    CREATOR_NODE_TYPES,
    get_edge_type_definition,
    get_schema_migration_sql,
    validate_edge_compatibility,
    validate_edge_type,
    validate_node_attrs,
    validate_node_type,
)
from .store import KGEdge, KGNode, KGStore


class CreatorKGStore(KGStore):
    """Extended KGStore with creator-focused schema and operations."""

    def __init__(self, path: str = ":memory:"):
        """Initialize creator KG store with schema validation."""
        super().__init__(path)
        self._apply_schema_migrations()

    def _apply_schema_migrations(self) -> None:
        """Apply schema migrations for creator extensions."""
        cur = self.conn.cursor()
        for sql in get_schema_migration_sql():
            cur.execute(sql)
        self.conn.commit()

    def add_creator_node(
        self,
        tenant: str,
        node_type: str,
        name: str,
        attrs: dict[str, Any] | None = None,
        created_at: str = "",
    ) -> int:
        """Add a node with creator schema validation."""
        # Validate node type
        if not validate_node_type(node_type):
            raise ValueError(f"Invalid node type: {node_type}")

        # Validate attributes
        attrs = attrs or {}
        is_valid, errors = validate_node_attrs(node_type, attrs)
        if not is_valid:
            raise ValueError(f"Invalid node attributes: {', '.join(errors)}")

        return self.add_node(tenant, node_type, name, attrs, created_at)

    def add_creator_edge(
        self,
        src_id: int,
        dst_id: int,
        edge_type: str,
        *,
        weight: float = 1.0,
        provenance_id: int | None = None,
        created_at: str = "",
    ) -> int:
        """Add an edge with creator schema validation."""
        # Validate edge type
        if not validate_edge_type(edge_type):
            raise ValueError(f"Invalid edge type: {edge_type}")

        # Get source and destination nodes
        src_node = self.get_node(src_id)
        dst_node = self.get_node(dst_id)
        if not src_node or not dst_node:
            raise ValueError("Source or destination node not found")

        # Validate edge compatibility
        if not validate_edge_compatibility(edge_type, src_node.type, dst_node.type):
            raise ValueError(
                f"Edge type '{edge_type}' not compatible with "
                f"source type '{src_node.type}' and destination type '{dst_node.type}'"
            )

        # Validate weight range
        edge_def = get_edge_type_definition(edge_type)
        if edge_def:
            min_weight, max_weight = edge_def.weight_range
            if not (min_weight <= weight <= max_weight):
                raise ValueError(
                    f"Weight {weight} outside valid range [{min_weight}, {max_weight}] for edge type '{edge_type}'"
                )

        return self.add_edge(
            src_id,
            dst_id,
            edge_type,
            weight=weight,
            provenance_id=provenance_id,
            created_at=created_at,
        )

    def get_creator_nodes(self, tenant: str, node_type: str | None = None, limit: int = 100) -> list[KGNode]:
        """Get creator nodes with optional type filtering."""
        if node_type and not validate_node_type(node_type):
            raise ValueError(f"Invalid node type: {node_type}")

        nodes = self.query_nodes(tenant, type=node_type)
        return nodes[:limit]

    def get_creator_edges(self, edge_type: str | None = None, limit: int = 100) -> list[KGEdge]:
        """Get creator edges with optional type filtering."""
        if edge_type and not validate_edge_type(edge_type):
            raise ValueError(f"Invalid edge type: {edge_type}")

        edges = self.query_edges(type=edge_type)
        return edges[:limit]

    def get_episode_timeline(self, tenant: str, creator_id: int, limit: int = 50) -> list[KGNode]:
        """Get timeline of episodes for a creator."""
        # Get creator node
        creator = self.get_node(creator_id)
        if not creator or creator.type != "creator":
            raise ValueError("Invalid creator node")

        # Get episodes hosted by this creator
        episode_edges = self.query_edges(src_id=creator_id, type="hosts")
        episode_ids = [edge.dst_id for edge in episode_edges]

        if not episode_ids:
            return []

        # Get episode nodes ordered by upload date
        cur = self.conn.cursor()
        placeholders = ",".join(["?"] * len(episode_ids))
        query = f"""
            SELECT * FROM kg_nodes
            WHERE id IN ({placeholders})
            AND tenant = ?
            AND type = 'episode'
            ORDER BY json_extract(attrs_json, '$.upload_date') DESC
            LIMIT ?
        """
        cur.execute(query, [*episode_ids, tenant, limit])
        rows = cur.fetchall()
        return [KGNode(**row) for row in rows]

    def get_episode_highlights(self, tenant: str, episode_id: int, limit: int = 20) -> list[KGNode]:
        """Get highlights for a specific episode."""
        # Get episode node
        episode = self.get_node(episode_id)
        if not episode or episode.type != "episode":
            raise ValueError("Invalid episode node")

        # Get highlight edges
        highlight_edges = self.query_edges(src_id=episode_id, type="contains_highlight")
        highlight_ids = [edge.dst_id for edge in highlight_edges]

        if not highlight_ids:
            return []

        # Get highlight nodes ordered by start time
        cur = self.conn.cursor()
        placeholders = ",".join(["?"] * len(highlight_ids))
        query = f"""
            SELECT * FROM kg_nodes
            WHERE id IN ({placeholders})
            AND tenant = ?
            AND type = 'highlight'
            ORDER BY json_extract(attrs_json, '$.start_time') ASC
            LIMIT ?
        """
        cur.execute(query, [*highlight_ids, tenant, limit])
        rows = cur.fetchall()
        return [KGNode(**row) for row in rows]

    def get_creator_collaborations(self, tenant: str, creator_id: int, limit: int = 20) -> list[tuple[KGNode, KGNode]]:
        """Get collaborations for a creator."""
        # Get creator node
        creator = self.get_node(creator_id)
        if not creator or creator.type != "creator":
            raise ValueError("Invalid creator node")

        # Get collaboration edges
        collab_edges = self.query_edges(src_id=creator_id, type="collaborates_with")
        collab_ids = [edge.dst_id for edge in collab_edges]

        if not collab_ids:
            return []

        # Get collaborator nodes
        cur = self.conn.cursor()
        placeholders = ",".join(["?"] * len(collab_ids))
        query = f"""
            SELECT * FROM kg_nodes
            WHERE id IN ({placeholders})
            AND tenant = ?
            AND type = 'creator'
            LIMIT ?
        """
        cur.execute(query, [*collab_ids, tenant, limit])
        rows = cur.fetchall()
        collaborators = [KGNode(**row) for row in rows]

        # Return tuples of (creator, collaborator)
        return [(creator, collab) for collab in collaborators]

    def get_topic_mentions(self, tenant: str, topic_id: int, limit: int = 50) -> list[tuple[KGNode, KGNode]]:
        """Get episodes that mention a specific topic."""
        # Get topic node
        topic = self.get_node(topic_id)
        if not topic or topic.type != "topic":
            raise ValueError("Invalid topic node")

        # Get discussion edges
        discussion_edges = self.query_edges(dst_id=topic_id, type="discusses")
        episode_ids = [edge.src_id for edge in discussion_edges]

        if not episode_ids:
            return []

        # Get episode nodes
        cur = self.conn.cursor()
        placeholders = ",".join(["?"] * len(episode_ids))
        query = f"""
            SELECT * FROM kg_nodes
            WHERE id IN ({placeholders})
            AND tenant = ?
            AND type = 'episode'
            ORDER BY json_extract(attrs_json, '$.upload_date') DESC
            LIMIT ?
        """
        cur.execute(query, [*episode_ids, tenant, limit])
        rows = cur.fetchall()
        episodes = [KGNode(**row) for row in rows]

        # Return tuples of (episode, topic)
        return [(episode, topic) for episode in episodes]

    def get_narrative_timeline(self, tenant: str, narrative_id: int, limit: int = 100) -> list[tuple[KGNode, str]]:
        """Get timeline of content related to a narrative."""
        # Get narrative node
        narrative = self.get_node(narrative_id)
        if not narrative or narrative.type != "narrative":
            raise ValueError("Invalid narrative node")

        # Get narrative edges
        narrative_edges = self.query_edges(dst_id=narrative_id, type="part_of_narrative")
        content_ids = [edge.src_id for edge in narrative_edges]

        if not content_ids:
            return []

        # Get content nodes ordered by date
        cur = self.conn.cursor()
        placeholders = ",".join(["?"] * len(content_ids))
        query = f"""
            SELECT *, json_extract(attrs_json, '$.upload_date') as content_date
            FROM kg_nodes
            WHERE id IN ({placeholders})
            AND tenant = ?
            AND type IN ('episode', 'claim', 'quote')
            ORDER BY content_date DESC
            LIMIT ?
        """
        cur.execute(query, [*content_ids, tenant, limit])
        rows = cur.fetchall()

        # Return tuples of (content_node, content_type)
        return [(KGNode(**row), row["type"]) for row in rows]

    def get_claim_verification_graph(self, tenant: str, claim_id: int, depth: int = 2) -> dict[str, list[KGNode]]:
        """Get verification graph for a claim (supporting/contradicting claims)."""
        # Get claim node
        claim = self.get_node(claim_id)
        if not claim or claim.type != "claim":
            raise ValueError("Invalid claim node")

        # Get supporting and contradicting claims
        supporting_edges = self.query_edges(src_id=claim_id, type="supports")
        contradicting_edges = self.query_edges(src_id=claim_id, type="contradicts")

        supporting_ids = [edge.dst_id for edge in supporting_edges]
        contradicting_ids = [edge.dst_id for edge in contradicting_edges]

        # Get supporting claims
        supporting_claims = []
        if supporting_ids:
            cur = self.conn.cursor()
            placeholders = ",".join(["?"] * len(supporting_ids))
            query = f"""
                SELECT * FROM kg_nodes
                WHERE id IN ({placeholders})
                AND tenant = ?
                AND type = 'claim'
            """
            cur.execute(query, [*supporting_ids, tenant])
            rows = cur.fetchall()
            supporting_claims = [KGNode(**row) for row in rows]

        # Get contradicting claims
        contradicting_claims = []
        if contradicting_ids:
            cur = self.conn.cursor()
            placeholders = ",".join(["?"] * len(contradicting_ids))
            query = f"""
                SELECT * FROM kg_nodes
                WHERE id IN ({placeholders})
                AND tenant = ?
                AND type = 'claim'
            """
            cur.execute(query, [*contradicting_ids, tenant])
            rows = cur.fetchall()
            contradicting_claims = [KGNode(**row) for row in rows]

        return {
            "original_claim": [claim],
            "supporting_claims": supporting_claims,
            "contradicting_claims": contradicting_claims,
        }

    def validate_schema_integrity(self) -> dict[str, Any]:
        """Validate the integrity of the creator schema."""
        results = {}
        cur = self.conn.cursor()

        # Define validation queries with clear names
        validation_queries = [
            (
                "orphaned_edges",
                """
                SELECT COUNT(*) as orphaned_edges
                FROM kg_edges e
                LEFT JOIN kg_nodes n1 ON e.src_id = n1.id
                LEFT JOIN kg_nodes n2 ON e.dst_id = n2.id
                WHERE n1.id IS NULL OR n2.id IS NULL
            """,
            ),
            (
                "invalid_node_types",
                f"""
                SELECT COUNT(*) as invalid_node_types
                FROM kg_nodes n
                WHERE n.type NOT IN ({", ".join(f"'{nt.name}'" for nt in CREATOR_NODE_TYPES)})
            """,
            ),
            (
                "invalid_edge_types",
                f"""
                SELECT COUNT(*) as invalid_edge_types
                FROM kg_edges e
                WHERE e.type NOT IN ({", ".join(f"'{et.name}'" for et in CREATOR_EDGE_TYPES)})
            """,
            ),
        ]

        for query_name, query in validation_queries:
            cur.execute(query)
            row = cur.fetchone()
            if row:
                results[query_name] = row[0]

        return results

    def get_schema_stats(self) -> dict[str, Any]:
        """Get statistics about the creator schema usage."""
        cur = self.conn.cursor()

        # Node type counts
        node_counts = {}
        for node_type in CREATOR_NODE_TYPES:
            cur.execute("SELECT COUNT(*) FROM kg_nodes WHERE type = ?", (node_type.name,))
            node_counts[node_type.name] = cur.fetchone()[0]

        # Edge type counts
        edge_counts = {}
        for edge_type in CREATOR_EDGE_TYPES:
            cur.execute("SELECT COUNT(*) FROM kg_edges WHERE type = ?", (edge_type.name,))
            edge_counts[edge_type.name] = cur.fetchone()[0]

        # Total counts
        cur.execute("SELECT COUNT(*) FROM kg_nodes")
        total_nodes = cur.fetchone()[0]

        cur.execute("SELECT COUNT(*) FROM kg_edges")
        total_edges = cur.fetchone()[0]

        return {
            "total_nodes": total_nodes,
            "total_edges": total_edges,
            "node_type_counts": node_counts,
            "edge_type_counts": edge_counts,
            "schema_version": "1.0.0",
        }
