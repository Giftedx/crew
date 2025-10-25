"""Tests for Neo4j knowledge graph store."""

import pytest

try:
    from neo4j import GraphDatabase
    NEO4J_AVAILABLE = True
except ImportError:
    NEO4J_AVAILABLE = False


@pytest.mark.skipif(not NEO4J_AVAILABLE, reason="Neo4j driver not available")
class TestNeo4jKGStore:
    """Test cases for Neo4j knowledge graph store."""

    @pytest.fixture
    def store(self):
        """Create Neo4j store instance."""
        from src.kg.neo4j.store import Neo4jKGStore
        store = Neo4jKGStore(
            uri="bolt://localhost:7687",
            user="neo4j",
            password="password"
        )
        yield store
        store.close()

    def test_store_initialization(self, store):
        """Test store initialization."""
        assert store is not None
        assert store.driver is not None

    def test_add_node(self, store):
        """Test adding a node."""
        node_id = store.add_node(
            tenant="test",
            type="Person",
            name="Test Person",
            attrs={"age": 30},
            created_at="2024-01-01"
        )
        assert node_id > 0

    def test_query_nodes(self, store):
        """Test querying nodes."""
        # Add test node
        store.add_node(
            tenant="test",
            type="Person",
            name="Query Test",
            attrs={"role": "developer"}
        )
        
        # Query nodes
        nodes = store.query_nodes("test", type="Person")
        assert len(nodes) > 0
        assert any(n.name == "Query Test" for n in nodes)

    def test_get_node(self, store):
        """Test getting a node by ID."""
        node_id = store.add_node(
            tenant="test",
            type="Organization",
            name="Test Org"
        )
        
        node = store.get_node(node_id)
        assert node is not None
        assert node.name == "Test Org"
        assert node.type == "Organization"

    def test_add_edge(self, store):
        """Test adding an edge."""
        # Create two nodes
        src_id = store.add_node("test", "Person", "Alice")
        dst_id = store.add_node("test", "Person", "Bob")
        
        # Add edge
        edge_id = store.add_edge(
            src_id=src_id,
            dst_id=dst_id,
            type="KNOWS",
            weight=0.8
        )
        assert edge_id > 0

    def test_query_edges(self, store):
        """Test querying edges."""
        # Create nodes and edge
        src_id = store.add_node("test", "Person", "Charlie")
        dst_id = store.add_node("test", "Person", "David")
        store.add_edge(src_id, dst_id, "WORKS_WITH")
        
        # Query edges
        edges = store.query_edges(src_id=src_id)
        assert len(edges) > 0
        assert any(e.type == "WORKS_WITH" for e in edges)

    def test_neighbors(self, store):
        """Test finding neighbors."""
        # Create nodes
        center_id = store.add_node("test", "Person", "Center")
        neighbor1_id = store.add_node("test", "Person", "Neighbor1")
        neighbor2_id = store.add_node("test", "Person", "Neighbor2")
        
        # Add edges
        store.add_edge(center_id, neighbor1_id, "CONNECTED")
        store.add_edge(center_id, neighbor2_id, "CONNECTED")
        
        # Find neighbors
        neighbors = list(store.neighbors(center_id, depth=1))
        assert len(neighbors) == 2
        assert neighbor1_id in neighbors
        assert neighbor2_id in neighbors

    def test_cypher_query(self, store):
        """Test custom Cypher query."""
        # Add test data
        store.add_node("test", "Entity", "TestEntity")
        
        # Execute Cypher query
        result = store.cypher_query(
            "MATCH (n:Node {tenant: $tenant}) RETURN count(n) as count",
            tenant="test"
        )
        assert len(result) > 0
        assert result[0]["count"] > 0

    def test_get_relationship_graph(self, store):
        """Test getting relationship graph."""
        # Create small graph
        center_id = store.add_node("test", "Person", "Center")
        neighbor_id = store.add_node("test", "Person", "Neighbor")
        store.add_edge(center_id, neighbor_id, "RELATES")
        
        # Get graph
        graph = store.get_relationship_graph(center_id, max_depth=1)
        assert "nodes" in graph
        assert "edges" in graph
        assert len(graph["nodes"]) >= 2
        assert len(graph["edges"]) >= 1

    def test_neighbors_depth_validation(self, store):
        """Test that neighbors() validates depth parameter to prevent injection."""
        center_id = store.add_node("test", "Person", "TestPerson")
        
        # Test invalid depth (too large)
        with pytest.raises(ValueError, match="Invalid depth: must be an integer between 1 and 10"):
            list(store.neighbors(center_id, depth=100))
        
        # Test invalid depth (negative)
        with pytest.raises(ValueError, match="Invalid depth: must be an integer between 1 and 10"):
            list(store.neighbors(center_id, depth=-1))
        
        # Test invalid depth (zero)
        with pytest.raises(ValueError, match="Invalid depth: must be an integer between 1 and 10"):
            list(store.neighbors(center_id, depth=0))
        
        # Test valid depth (should not raise)
        neighbors = list(store.neighbors(center_id, depth=1))
        assert isinstance(neighbors, list)

    def test_relationship_graph_depth_validation(self, store):
        """Test that get_relationship_graph() validates max_depth to prevent injection."""
        center_id = store.add_node("test", "Person", "TestPerson")
        
        # Test invalid max_depth (too large)
        with pytest.raises(ValueError, match="Invalid max_depth: must be an integer between 1 and 10"):
            store.get_relationship_graph(center_id, max_depth=100)
        
        # Test invalid max_depth (negative)
        with pytest.raises(ValueError, match="Invalid max_depth: must be an integer between 1 and 10"):
            store.get_relationship_graph(center_id, max_depth=-1)
        
        # Test invalid max_depth (zero)
        with pytest.raises(ValueError, match="Invalid max_depth: must be an integer between 1 and 10"):
            store.get_relationship_graph(center_id, max_depth=0)
        
        # Test valid max_depth (should not raise)
        graph = store.get_relationship_graph(center_id, max_depth=2)
        assert isinstance(graph, dict)
        assert "nodes" in graph
        assert "edges" in graph
