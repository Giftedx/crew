"""Enhanced knowledge graph system with advanced reasoning and learning capabilities.

This module extends the existing knowledge graph with advanced features including:
- Multi-hop reasoning and path finding
- Temporal reasoning and trend analysis
- Entity relationship strength calculation
- Advanced query capabilities with semantic search
- Knowledge consolidation and pruning
- Cross-domain knowledge integration
"""

from __future__ import annotations

import json
import logging
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from typing import Any

import numpy as np

from kg.store import KGEdge, KGNode, KGStore

logger = logging.getLogger(__name__)


@dataclass
class KnowledgePath:
    """Represents a path through the knowledge graph."""

    nodes: list[KGNode]
    edges: list[KGEdge]
    total_weight: float
    path_type: str  # "direct", "inference", "temporal", "causal"
    confidence: float


@dataclass
class EntityProfile:
    """Enhanced entity profile with temporal and relational data."""

    node: KGNode
    relationships: dict[str, list[KGEdge]] = field(default_factory=dict)
    temporal_activity: dict[str, float] = field(default_factory=dict)  # period -> activity_score
    importance_score: float = 0.0
    trust_score: float = 0.5
    last_updated: float = field(default_factory=time.time)


@dataclass
class ReasoningContext:
    """Context for advanced reasoning operations."""

    query_entities: list[str]
    relationship_types: list[str] | None = None
    time_window: tuple[float, float] | None = None
    max_hops: int = 3
    min_confidence: float = 0.3
    include_temporal: bool = True


class EnhancedKnowledgeGraph:
    """Enhanced knowledge graph with advanced reasoning capabilities."""

    def __init__(self, store: KGStore):
        self.store = store
        self.entity_profiles: dict[str, EntityProfile] = {}
        self.relationship_cache: dict[str, list[KGEdge]] = {}

        # Performance tracking
        self.query_stats = {
            "total_queries": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "avg_response_time": 0.0,
        }

    def query_entity_profile(self, entity_name: str, tenant: str) -> EntityProfile | None:
        """Get enhanced entity profile with relationships and metadata."""
        self.query_stats["total_queries"] += 1
        start_time = time.time()

        try:
            # Check cache first
            cache_key = f"{tenant}:{entity_name}"
            if cache_key in self.entity_profiles:
                self.query_stats["cache_hits"] += 1
                return self.entity_profiles[cache_key]

            # Query nodes
            nodes = self.store.query_nodes(tenant, type="entity", name=entity_name)
            if not nodes:
                return None

            entity_node = nodes[0]

            # Get relationships
            relationships = self._get_entity_relationships(entity_node, tenant)

            # Calculate importance and trust scores
            importance_score = self._calculate_importance_score(entity_node, relationships, tenant)
            trust_score = self._calculate_trust_score(entity_node, relationships)

            # Get temporal activity
            temporal_activity = self._get_temporal_activity(entity_node, tenant)

            # Create profile
            profile = EntityProfile(
                node=entity_node,
                relationships=relationships,
                temporal_activity=temporal_activity,
                importance_score=importance_score,
                trust_score=trust_score,
            )

            # Cache profile
            self.entity_profiles[cache_key] = profile
            self.query_stats["cache_misses"] += 1

            # Update average response time
            response_time = time.time() - start_time
            self.query_stats["avg_response_time"] = (
                self.query_stats["avg_response_time"] * (self.query_stats["total_queries"] - 1) + response_time
            ) / self.query_stats["total_queries"]

            return profile

        except Exception as e:
            logger.error(f"Error querying entity profile: {e}")
            return None

    def _get_entity_relationships(self, entity_node: KGNode, tenant: str) -> dict[str, list[KGEdge]]:
        """Get all relationships for an entity."""
        cache_key = f"{tenant}:{entity_node.id}"
        if cache_key in self.relationship_cache:
            return self.relationship_cache[cache_key]

        relationships = defaultdict(list)

        # Query outgoing edges
        outgoing_edges = self.store.query_edges(src_id=entity_node.id or 0)
        for edge in outgoing_edges:
            relationships[edge.type].append(edge)

        # Query incoming edges
        incoming_edges = self.store.query_edges(dst_id=entity_node.id or 0)
        for edge in incoming_edges:
            relationships[f"incoming_{edge.type}"].append(edge)

        self.relationship_cache[cache_key] = dict(relationships)
        return dict(relationships)

    def _calculate_importance_score(
        self, entity_node: KGNode, relationships: dict[str, list[KGEdge]], tenant: str
    ) -> float:
        """Calculate importance score for an entity."""
        score = 0.0

        # Base score from node attributes
        attrs = json.loads(entity_node.attrs_json)
        base_importance = attrs.get("importance", 0.5)
        score += base_importance * 0.3

        # Relationship count score
        total_relationships = sum(len(edges) for edges in relationships.values())
        relationship_score = min(total_relationships / 10.0, 1.0)  # Cap at 10 relationships
        score += relationship_score * 0.4

        # Temporal activity score
        recent_activity = sum(
            activity
            for period, activity in self._get_temporal_activity(entity_node, tenant).items()
            if period.startswith("last_")
        )
        activity_score = min(recent_activity / 5.0, 1.0)  # Cap at 5 recent activities
        score += activity_score * 0.3

        return min(score, 1.0)

    def _calculate_trust_score(self, entity_node: KGNode, relationships: dict[str, list[KGEdge]]) -> float:
        """Calculate trust score for an entity."""
        # Base trust from verification sources
        attrs = json.loads(entity_node.attrs_json)
        base_trust = attrs.get("trust_score", 0.5)

        # Adjust based on relationship quality
        verification_edges = relationships.get("verification", [])
        if verification_edges:
            # Higher trust if verified by multiple sources
            trust_multiplier = min(len(verification_edges) / 3.0, 1.5)
            base_trust *= trust_multiplier

        return min(base_trust, 1.0)

    def _get_temporal_activity(self, entity_node: KGNode, tenant: str) -> dict[str, float]:
        """Get temporal activity patterns for an entity."""
        activity = {
            "last_hour": 0.0,
            "last_day": 0.0,
            "last_week": 0.0,
            "last_month": 0.0,
        }

        # This would analyze edge creation times
        # For now, return placeholder data
        return activity

    def find_reasoning_paths(
        self, start_entity: str, end_entity: str, context: ReasoningContext, tenant: str
    ) -> list[KnowledgePath]:
        """Find reasoning paths between entities."""
        paths = []

        # Get entity nodes
        start_nodes = self.store.query_nodes(tenant, type="entity", name=start_entity)
        end_nodes = self.store.query_nodes(tenant, type="entity", name=end_entity)

        if not start_nodes or not end_nodes:
            return paths

        start_node = start_nodes[0]
        # end_node could be used for bidirectional search optimization
        _ = end_nodes[0]

        # Use BFS to find paths
        visited = set()
        queue = deque([(start_node, [], 0.0)])

        while queue:
            current_node, path_edges, path_weight = queue.popleft()
            current_id = current_node.id or 0

            if current_id in visited:
                continue
            visited.add(current_id)

            # Check if we reached the end
            if current_node.name == end_entity:
                path = KnowledgePath(
                    nodes=[start_node] + [edge.dst_id for edge in path_edges],
                    edges=path_edges,
                    total_weight=path_weight,
                    path_type="direct",
                    confidence=self._calculate_path_confidence(path_edges),
                )
                paths.append(path)
                continue

            # Explore neighbors
            neighbors = self.store.neighbors(current_id, tenant)
            for neighbor_id in neighbors:
                if neighbor_id in visited:
                    continue

                # Get edge between current and neighbor
                edges = self.store.query_edges(src_id=current_id, dst_id=neighbor_id)
                if not edges:
                    continue

                edge = edges[0]

                # Check relationship type filter
                if context.relationship_types and edge.type not in context.relationship_types:
                    continue

                # Check hop limit
                if len(path_edges) >= context.max_hops:
                    continue

                new_path_edges = path_edges + [edge]
                new_weight = path_weight + edge.weight

                queue.append((self.store.get_node(neighbor_id), new_path_edges, new_weight))

        return paths

    def _calculate_path_confidence(self, edges: list[KGEdge]) -> float:
        """Calculate confidence score for a reasoning path."""
        if not edges:
            return 0.0

        # Average edge weight as base confidence
        avg_weight = sum(edge.weight for edge in edges) / len(edges)

        # Penalize long paths
        length_penalty = max(0.5, 1.0 - (len(edges) - 1) * 0.1)

        return avg_weight * length_penalty

    def perform_temporal_reasoning(self, entity_name: str, tenant: str, time_window_days: int = 30) -> dict[str, Any]:
        """Perform temporal reasoning on entity evolution."""
        profile = self.query_entity_profile(entity_name, tenant)
        if not profile:
            return {"error": "Entity not found"}

        # Analyze temporal patterns
        temporal_analysis = {
            "entity_name": entity_name,
            "time_window_days": time_window_days,
            "activity_trends": {},
            "relationship_evolution": {},
            "importance_trends": [],
        }

        # This would analyze historical data
        # For now, return placeholder analysis
        return temporal_analysis

    def find_similar_entities(
        self, entity_name: str, tenant: str, limit: int = 10, similarity_threshold: float = 0.7
    ) -> list[tuple[EntityProfile, float]]:
        """Find entities similar to the given entity."""
        target_profile = self.query_entity_profile(entity_name, tenant)
        if not target_profile:
            return []

        similar_entities = []

        # Get all entities in tenant
        all_nodes = self.store.query_nodes(tenant, type="entity")

        for node in all_nodes:
            if node.name == entity_name:
                continue

            # Calculate similarity
            similarity = self._calculate_entity_similarity(target_profile, node, tenant)
            if similarity >= similarity_threshold:
                profile = self.query_entity_profile(node.name, tenant)
                if profile:
                    similar_entities.append((profile, similarity))

        # Sort by similarity and return top results
        similar_entities.sort(key=lambda x: x[1], reverse=True)
        return similar_entities[:limit]

    def _calculate_entity_similarity(self, profile1: EntityProfile, node2: KGNode, tenant: str) -> float:
        """Calculate similarity between two entities."""
        # Get profile for second entity
        profile2 = self.query_entity_profile(node2.name, tenant)
        if not profile2:
            return 0.0

        # Calculate similarity based on multiple factors
        similarity_factors = []

        # Relationship overlap
        rel_overlap = self._calculate_relationship_overlap(profile1, profile2)
        similarity_factors.append(("relationships", rel_overlap, 0.4))

        # Temporal activity similarity
        temp_similarity = self._calculate_temporal_similarity(profile1, profile2)
        similarity_factors.append(("temporal", temp_similarity, 0.3))

        # Attribute similarity (name, type, etc.)
        attr_similarity = self._calculate_attribute_similarity(profile1.node, profile2.node)
        similarity_factors.append(("attributes", attr_similarity, 0.3))

        # Calculate weighted similarity
        total_similarity = sum(factor * weight for _, factor, weight in similarity_factors)

        return total_similarity

    def _calculate_relationship_overlap(self, profile1: EntityProfile, profile2: EntityProfile) -> float:
        """Calculate overlap in entity relationships."""
        rel_types1 = set(profile1.relationships.keys())
        rel_types2 = set(profile2.relationships.keys())

        if not rel_types1 and not rel_types2:
            return 1.0

        intersection = rel_types1.intersection(rel_types2)
        union = rel_types1.union(rel_types2)

        return len(intersection) / len(union) if union else 0.0

    def _calculate_temporal_similarity(self, profile1: EntityProfile, profile2: EntityProfile) -> float:
        """Calculate similarity in temporal activity patterns."""
        # Simple cosine similarity of activity vectors
        activities1 = list(profile1.temporal_activity.values())
        activities2 = list(profile2.temporal_activity.values())

        if not activities1 or not activities2:
            return 0.5  # Neutral similarity

        # Pad shorter vector
        max_len = max(len(activities1), len(activities2))
        if len(activities1) < max_len:
            activities1.extend([0.0] * (max_len - len(activities1)))
        if len(activities2) < max_len:
            activities2.extend([0.0] * (max_len - len(activities2)))

        # Calculate cosine similarity
        dot_product = sum(a * b for a, b in zip(activities1, activities2))
        norm1 = np.sqrt(sum(a * a for a in activities1))
        norm2 = np.sqrt(sum(b * b for b in activities2))

        if norm1 == 0 or norm2 == 0:
            return 0.0

        return dot_product / (norm1 * norm2)

    def _calculate_attribute_similarity(self, node1: KGNode, node2: KGNode) -> float:
        """Calculate similarity based on node attributes."""
        attrs1 = json.loads(node1.attrs_json)
        attrs2 = json.loads(node2.attrs_json)

        # Simple attribute overlap
        common_attrs = set(attrs1.keys()).intersection(set(attrs2.keys()))
        total_attrs = set(attrs1.keys()).union(set(attrs2.keys()))

        if not total_attrs:
            return 1.0

        return len(common_attrs) / len(total_attrs)

    def consolidate_knowledge(
        self, entity_name: str, tenant: str, consolidation_strategy: str = "merge"
    ) -> dict[str, Any]:
        """Consolidate knowledge for an entity using advanced algorithms."""
        profile = self.query_entity_profile(entity_name, tenant)
        if not profile:
            return {"error": "Entity not found"}

        if consolidation_strategy == "merge":
            return self._merge_similar_entities(profile, tenant)
        elif consolidation_strategy == "prune":
            return self._prune_redundant_knowledge(profile, tenant)
        else:
            return {"error": f"Unknown consolidation strategy: {consolidation_strategy}"}

    def _merge_similar_entities(self, profile: EntityProfile, tenant: str) -> dict[str, Any]:
        """Merge similar entities to reduce redundancy."""
        # Find similar entities
        similar_entities = self.find_similar_entities(profile.node.name, tenant, limit=5, similarity_threshold=0.8)

        merge_candidates = []
        for similar_profile, similarity in similar_entities:
            if similarity > 0.9:  # Very high similarity
                merge_candidates.append(
                    {
                        "entity": similar_profile.node.name,
                        "similarity": similarity,
                        "relationships_count": sum(len(edges) for edges in similar_profile.relationships.values()),
                    }
                )

        return {
            "entity": profile.node.name,
            "merge_candidates": merge_candidates,
            "estimated_reductions": len(merge_candidates),
        }

    def _prune_redundant_knowledge(self, profile: EntityProfile, tenant: str) -> dict[str, Any]:
        """Prune redundant or low-value knowledge."""
        pruning_candidates = []

        # Identify low-confidence relationships
        for rel_type, edges in profile.relationships.items():
            for edge in edges:
                if edge.weight < 0.3:  # Low confidence
                    pruning_candidates.append(
                        {
                            "relationship": rel_type,
                            "target": self.store.get_node(edge.dst_id),
                            "confidence": edge.weight,
                            "reason": "low_confidence",
                        }
                    )

        return {
            "entity": profile.node.name,
            "pruning_candidates": pruning_candidates,
            "estimated_removals": len(pruning_candidates),
        }

    def get_knowledge_graph_stats(self, tenant: str) -> dict[str, Any]:
        """Get comprehensive knowledge graph statistics."""
        try:
            # Get all nodes and edges for tenant
            nodes = self.store.query_nodes(tenant)
            edges = self.store.query_edges(tenant=tenant)

            # Calculate statistics
            node_types = defaultdict(int)
            edge_types = defaultdict(int)
            entity_count = 0

            for node in nodes:
                node_types[node.type] += 1
                if node.type == "entity":
                    entity_count += 1

            for edge in edges:
                edge_types[edge.type] += 1

            return {
                "total_nodes": len(nodes),
                "total_edges": len(edges),
                "entity_count": entity_count,
                "node_types": dict(node_types),
                "edge_types": dict(edge_types),
                "average_relationships_per_entity": entity_count / len(edges) if edges else 0,
                "cache_stats": self.query_stats,
            }

        except Exception as e:
            logger.error(f"Error getting knowledge graph stats: {e}")
            return {"error": str(e)}

    def export_knowledge_graph(self, tenant: str, format: str = "json") -> dict[str, Any] | str:
        """Export knowledge graph in various formats."""
        try:
            nodes = self.store.query_nodes(tenant)
            edges = self.store.query_edges(tenant=tenant)

            if format == "json":
                return {
                    "nodes": [
                        {
                            "id": node.id,
                            "name": node.name,
                            "type": node.type,
                            "attributes": json.loads(node.attrs_json),
                            "created_at": node.created_at,
                        }
                        for node in nodes
                    ],
                    "edges": [
                        {
                            "id": edge.id,
                            "source": edge.src_id,
                            "target": edge.dst_id,
                            "type": edge.type,
                            "weight": edge.weight,
                            "provenance_id": edge.provenance_id,
                            "created_at": edge.created_at,
                        }
                        for edge in edges
                    ],
                    "metadata": {
                        "exported_at": time.time(),
                        "tenant": tenant,
                        "node_count": len(nodes),
                        "edge_count": len(edges),
                    },
                }

            elif format == "graphml":
                # Would implement GraphML export
                return {"error": "GraphML export not yet implemented"}

            else:
                return {"error": f"Unsupported export format: {format}"}

        except Exception as e:
            logger.error(f"Error exporting knowledge graph: {e}")
            return {"error": str(e)}


class AdvancedReasoningEngine:
    """Advanced reasoning engine for complex knowledge graph queries."""

    def __init__(self, knowledge_graph: EnhancedKnowledgeGraph):
        self.knowledge_graph = knowledge_graph
        self.reasoning_cache: dict[str, Any] = {}

    def answer_complex_query(self, query: str, context: ReasoningContext, tenant: str) -> dict[str, Any]:
        """Answer complex queries using knowledge graph reasoning."""
        cache_key = f"{tenant}:{hash(query)}:{context.max_hops}"
        if cache_key in self.reasoning_cache:
            return self.reasoning_cache[cache_key]

        # Parse query to extract entities
        entities = self._extract_entities_from_query(query)

        if len(entities) < 2:
            return {"error": "Query must reference at least two entities"}

        # Find reasoning paths between entities
        all_paths = []
        for i in range(len(entities) - 1):
            paths = self.knowledge_graph.find_reasoning_paths(entities[i], entities[i + 1], context, tenant)
            all_paths.extend(paths)

        # Rank and filter paths
        ranked_paths = self._rank_paths(all_paths, context)

        # Generate answer based on paths
        answer = self._generate_answer_from_paths(query, ranked_paths, tenant)

        # Cache result
        self.reasoning_cache[cache_key] = answer

        return answer

    def _extract_entities_from_query(self, query: str) -> list[str]:
        """Extract entity names from natural language query."""
        # Simple entity extraction - would be enhanced with NLP
        # For now, extract capitalized words as potential entities
        words = query.split()
        entities = []

        for word in words:
            # Look for capitalized words that might be entity names
            if word and word[0].isupper() and len(word) > 2 and not word.endswith(("?", "!", ".")):
                entities.append(word)

        return entities[:5]  # Limit to avoid too many entities

    def _rank_paths(self, paths: list[KnowledgePath], context: ReasoningContext) -> list[KnowledgePath]:
        """Rank and filter reasoning paths."""
        if not paths:
            return []

        # Filter by confidence
        filtered_paths = [path for path in paths if path.confidence >= context.min_confidence]

        # Sort by confidence and path length
        filtered_paths.sort(
            key=lambda p: (p.confidence, -len(p.edges)),  # Higher confidence, shorter paths first
            reverse=True,
        )

        # Limit results
        return filtered_paths[:10]

    def _generate_answer_from_paths(self, query: str, paths: list[KnowledgePath], tenant: str) -> dict[str, Any]:
        """Generate answer based on reasoning paths."""
        if not paths:
            return {
                "answer": "No clear relationship found between the queried entities.",
                "confidence": 0.0,
                "paths_analyzed": 0,
            }

        # Generate answer based on strongest path
        best_path = paths[0]

        answer_parts = []
        for i, edge in enumerate(best_path.edges):
            source_name = self._get_node_name(edge.src_id, tenant)
            target_name = self._get_node_name(edge.dst_id, tenant)

            answer_parts.append(f"{source_name} {edge.type.replace('_', ' ')} {target_name}")

        answer_text = " → ".join(answer_parts)

        return {
            "answer": f"Based on the knowledge graph: {answer_text}",
            "confidence": best_path.confidence,
            "paths_analyzed": len(paths),
            "best_path_length": len(best_path.edges),
            "path_type": best_path.path_type,
        }

    def _get_node_name(self, node_id: int, tenant: str) -> str:
        """Get node name from ID."""
        node = self.knowledge_graph.store.get_node(node_id)
        return node.name if node else f"node_{node_id}"


# Global enhanced knowledge graph instance
_enhanced_kg: EnhancedKnowledgeGraph | None = None


def get_enhanced_knowledge_graph(store_path: str = ":memory:") -> EnhancedKnowledgeGraph:
    """Get or create the global enhanced knowledge graph."""
    global _enhanced_kg

    if _enhanced_kg is None:
        store = KGStore(store_path)
        _enhanced_kg = EnhancedKnowledgeGraph(store)
    return _enhanced_kg


def initialize_enhanced_knowledge_graph(store_path: str = ":memory:") -> None:
    """Initialize the enhanced knowledge graph system."""
    global _enhanced_kg

    _enhanced_kg = EnhancedKnowledgeGraph(KGStore(store_path))
    logger.info("Enhanced knowledge graph initialized")


__all__ = [
    "EnhancedKnowledgeGraph",
    "AdvancedReasoningEngine",
    "KnowledgePath",
    "EntityProfile",
    "ReasoningContext",
    "get_enhanced_knowledge_graph",
    "initialize_enhanced_knowledge_graph",
]
