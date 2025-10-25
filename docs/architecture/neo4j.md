# Neo4j Graph Database Integration

Neo4j provides powerful graph database capabilities for relationship analysis, entity networks, and fact-checking graphs.

## Overview

The Neo4j integration enhances the knowledge graph system with:

- **Cypher Query Support**: Execute complex graph queries
- **Relationship Analysis**: Discover connections between entities
- **Scalable Performance**: Handle large-scale graphs efficiently
- **Multi-Tenant Support**: Tenant-isolated graph operations

## Architecture

### Data Model

```
(Node) -[RELATES]-> (Node)
  |
  |-- Properties: tenant, type, name, attrs_json, created_at
  |
(Relationship)
  |
  |-- Properties: type, weight, provenance_id, created_at
```

### Service Architecture

```
Neo4jKGStore
├── add_node()         # Create nodes
├── query_nodes()      # Query by criteria
├── add_edge()         # Create relationships
├── query_edges()      # Query relationships
├── neighbors()        # Find connected nodes
├── cypher_query()     # Custom Cypher queries
└── get_relationship_graph()  # Subgraph extraction
```

## Configuration

### Environment Variables

```bash
# Neo4j Connection
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_password
NEO4J_DATABASE=neo4j

# Feature Flag
ENABLE_NEO4J_GRAPH=true
```

### Docker Compose

Neo4j is configured in `docker-compose.yml`:

```yaml
neo4j:
  image: neo4j:5.14
  ports:
    - "7474:7474"  # HTTP UI
    - "7687:7687"  # Bolt protocol
  environment:
    - NEO4J_AUTH=neo4j/${NEO4J_PASSWORD}
    - NEO4J_PLUGINS=["apoc"]
```

## Usage

### Basic Operations

```python
from src.kg.neo4j.store import Neo4jKGStore

# Initialize store
store = Neo4jKGStore(
    uri="bolt://localhost:7687",
    user="neo4j",
    password="password"
)

# Add a node
node_id = store.add_node(
    tenant="test",
    type="Person",
    name="John Doe",
    attrs={"age": 30, "role": "developer"}
)

# Add an edge
src_id = store.add_node("test", "Person", "Alice")
dst_id = store.add_node("test", "Person", "Bob")
edge_id = store.add_edge(src_id, dst_id, "KNOWS", weight=0.9)

# Query nodes
nodes = store.query_nodes("test", type="Person")
for node in nodes:
    print(f"{node.name}: {node.type}")

# Find neighbors
neighbors = store.neighbors(node_id, depth=2)
for neighbor_id in neighbors:
    neighbor = store.get_node(neighbor_id)
    print(f"Connected to: {neighbor.name}")
```

### Advanced Cypher Queries

```python
# Find all connected nodes within 3 hops
result = store.cypher_query("""
    MATCH path = (start:Node)-[*1..3]->(connected:Node)
    WHERE start.name = $name
    RETURN DISTINCT connected.name as name, 
           length(path) as distance
    ORDER BY distance
""", name="John Doe")

# Analyze relationship strength
result = store.cypher_query("""
    MATCH (n:Node)-[r:RELATES]->(m:Node)
    WHERE n.tenant = $tenant
    RETURN n.name as from, m.name as to, 
           sum(r.weight) as total_weight
    ORDER BY total_weight DESC
    LIMIT 10
""", tenant="test")
```

### Relationship Graph Visualization

```python
# Get subgraph for visualization
graph = store.get_relationship_graph(node_id, max_depth=2)

# graph contains:
# {
#   "nodes": [
#     {"id": 1, "name": "Alice", "type": "Person"},
#     {"id": 2, "name": "Bob", "type": "Person"}
#   ],
#   "edges": [
#     {"src": "Alice", "dst": "Bob", "type": "KNOWS", "weight": 0.9}
#   ]
# }
```

## Use Cases

### 1. Entity Relationship Discovery

Discover connections between entities in debate content:

```python
# Find all people connected to a specific claim
claim_id = store.add_node("tenant", "Claim", "Climate change claim")
people = store.query_nodes("tenant", type="Person")

for person in people:
    # Add relationship if person made the claim
    store.add_edge(person.id, claim_id, "MADE_CLAIM")
```

### 2. Fact-Checking Graph

Build a graph of fact-checks and sources:

```python
# Create fact-check graph
fact_id = store.add_node("tenant", "Fact", "Fact statement")
source_id = store.add_node("tenant", "Source", "Authoritative source")
verification_id = store.add_node("tenant", "Verification", "Verified")

# Connect fact to source
store.add_edge(fact_id, source_id, "VERIFIED_BY")
store.add_edge(fact_id, verification_id, "VERIFICATION_STATUS")
```

### 3. Network Analysis

Analyze guest networks and connections:

```python
# Find influential nodes
result = store.cypher_query("""
    MATCH (n:Node)-[r:RELATES]->(m:Node)
    WHERE n.type = 'Person'
    WITH n, count(m) as connections
    ORDER BY connections DESC
    LIMIT 10
    RETURN n.name, connections
""")
```

## Performance Considerations

### Indexing

The service automatically creates indexes:

- `(tenant, name)` unique constraint
- `tenant` index for faster filtering
- `type` index for category queries

### Memory Configuration

Configure memory in Docker:

```yaml
environment:
  - NEO4J_dbms_memory_heap_max__size=512m
  - NEO4J_dbms_memory_pagecache_size=256m
```

### Query Optimization

- Use parameterized queries for reuse
- Limit result sets with `LIMIT`
- Use indexes for WHERE clauses
- Avoid deep traversals (>5 hops)

## Monitoring

### Health Checks

Neo4j includes built-in health checks:

```bash
# Docker health check
docker-compose exec neo4j cypher-shell -u neo4j -p password "RETURN 1"
```

### Metrics

Monitor Neo4j metrics:

- **Page Cache Hit Ratio**: Should be > 95%
- **Transaction Log Size**: Monitor growth
- **Connection Pool**: Monitor active connections
- **Query Performance**: Track slow queries

## Troubleshooting

### Connection Issues

```bash
# Check Neo4j is running
docker-compose ps neo4j

# View logs
docker-compose logs neo4j

# Test connection
docker-compose exec neo4j cypher-shell -u neo4j -p password
```

### Performance Issues

1. **Check indexes**: Ensure indexes exist
2. **Review queries**: Profile slow queries
3. **Monitor memory**: Check heap usage
4. **Optimize graph**: Review relationship patterns

### Data Migration

Migrate from SQLite to Neo4j:

```python
from src.kg.store import KGStore
from src.kg.neo4j.store import Neo4jKGStore

# Connect to both stores
sqlite_store = KGStore("data/kg.db")
neo4j_store = Neo4jKGStore()

# Migrate nodes
for node in sqlite_store.query_nodes("tenant"):
    neo4j_store.add_node(
        tenant=node.tenant,
        type=node.type,
        name=node.name,
        attrs=json.loads(node.attrs_json),
        created_at=node.created_at
    )

# Migrate edges
for edge in sqlite_store.query_edges():
    neo4j_store.add_edge(
        src_id=edge.src_id,
        dst_id=edge.dst_id,
        type=edge.type,
        weight=edge.weight,
        provenance_id=edge.provenance_id,
        created_at=edge.created_at
    )
```

## See Also

- [Neo4j Documentation](https://neo4j.com/docs/)
- [Cypher Query Language](https://neo4j.com/docs/cypher-manual/)
- [Knowledge Graph Architecture](./knowledge_graph.md)
- [Configuration Guide](../configuration.md)
