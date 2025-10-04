# Fix #8: Add Graph Memory Query API - Implementation Plan

**Date:** 2025-01-03  
**Priority:** MEDIUM  
**Status:** IN PROGRESS  
**Estimated Effort:** ~250 lines of implementation

---

## Problem Statement

**Current State:**

- `GraphMemoryTool` can **store** graph structures (nodes, edges, keywords)
- Graphs saved to disk as JSON files in tenant-scoped directories
- **NO retrieval or query capabilities** - data is write-only

**Impact:**

- Stored knowledge graphs cannot be accessed or utilized
- No way to search for nodes by keywords
- No way to traverse relationships between entities
- No way to extract relevant subgraphs for context

**Example Use Case (Currently Impossible):**

```python
# User wants to find all content related to "AI safety"
# Currently: No way to query stored graphs
# Desired: search_graphs(query="AI safety", namespace="acme:main:graph")
```

---

## Solution Design

Add **3 core query methods** to `GraphMemoryTool`:

### 1. `search_graphs()` - Find Graphs by Query

**Purpose:** Search across stored graphs using keywords, metadata, or tags

**Signature:**

```python
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
        query: Text query to match against keywords, node labels
        namespace: Tenant-scoped namespace to search in
        tags: Filter by specific tags
        limit: Maximum number of results
        
    Returns:
        StepResult with:
            - graphs: List of matching graph metadata
            - count: Number of matches
            - namespace: Resolved namespace
    """
```

**Search Strategy:**

1. Load all JSON files from namespace directory
2. Parse metadata and keywords
3. Score each graph based on:
   - Keyword overlap with query
   - Tag matches
   - Metadata relevance
4. Return top N graphs by score

### 2. `get_graph()` - Retrieve Specific Graph

**Purpose:** Load a specific graph by ID for analysis

**Signature:**

```python
def get_graph(
    self,
    *,
    graph_id: str,
    namespace: str = "graph",
) -> StepResult:
    """Retrieve a specific graph by ID.
    
    Args:
        graph_id: UUID of the graph to retrieve
        namespace: Tenant-scoped namespace
        
    Returns:
        StepResult with:
            - graph_id: ID of retrieved graph
            - nodes: List of nodes
            - edges: List of edges
            - keywords: Extracted keywords
            - metadata: Graph metadata
    """
```

**Implementation:**

1. Resolve namespace (apply tenant context)
2. Construct file path: `{namespace_path}/{graph_id}.json`
3. Load and parse JSON
4. Return full graph structure

### 3. `traverse_graph()` - Navigate Relationships

**Purpose:** Find related nodes by following edges (path finding)

**Signature:**

```python
def traverse_graph(
    self,
    *,
    graph_id: str,
    start_node: str,
    max_depth: int = 3,
    relation_filter: list[str] | None = None,
    namespace: str = "graph",
) -> StepResult:
    """Traverse graph from a starting node.
    
    Args:
        graph_id: UUID of the graph
        start_node: Node ID to start from (e.g., "keyword_AI")
        max_depth: Maximum edge hops
        relation_filter: Only follow edges with these relations
        namespace: Tenant-scoped namespace
        
    Returns:
        StepResult with:
            - visited_nodes: List of reached nodes
            - paths: List of paths from start to each node
            - subgraph: Extracted subgraph containing visited nodes/edges
    """
```

**Traversal Algorithm:**

1. Load graph by ID
2. Use BFS/DFS from start_node
3. Follow edges up to max_depth
4. Filter by relation types if specified
5. Return visited nodes and paths

---

## Implementation Plan

### Phase 1: Add `search_graphs()` Method

**File:** `src/ultimate_discord_intelligence_bot/tools/graph_memory_tool.py`

**Estimated Lines:** ~80 lines

**Implementation:**

```python
def search_graphs(
    self,
    *,
    query: str | None = None,
    namespace: str = "graph",
    tags: list[str] | None = None,
    limit: int = 10,
) -> StepResult:
    """Search for graphs matching query/tags."""
    namespace, tenant_scoped = self._resolve_namespace(namespace)
    ns_path = self._namespace_path(namespace)
    
    if not ns_path.exists() or not any(ns_path.glob("*.json")):
        return StepResult.ok(graphs=[], count=0, namespace=namespace)
    
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
            
            matches.append({
                "graph_id": json_file.stem,
                "score": score,
                "keywords": metadata.get("keywords", []),
                "tags": metadata.get("tags", []),
                "node_count": metadata.get("node_count", 0),
                "edge_count": metadata.get("edge_count", 0),
                "tenant_scoped": metadata.get("tenant_scoped", False),
            })
        except Exception:
            continue  # Skip corrupted files
    
    # Sort by score (descending) and limit
    matches.sort(key=lambda x: x["score"], reverse=True)
    results = matches[:limit]
    
    self._metrics.counter(
        "graph_memory_searches_total",
        labels={"namespace": namespace, "tenant_scoped": str(tenant_scoped).lower()},
    ).inc()
    
    return StepResult.ok(
        graphs=results,
        count=len(results),
        namespace=namespace,
        tenant_scoped=tenant_scoped,
    )
```

### Phase 2: Add `get_graph()` Method

**File:** `src/ultimate_discord_intelligence_bot/tools/graph_memory_tool.py`

**Estimated Lines:** ~40 lines

**Implementation:**

```python
def get_graph(
    self,
    *,
    graph_id: str,
    namespace: str = "graph",
) -> StepResult:
    """Retrieve a specific graph by ID."""
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
        
        self._metrics.counter(
            "graph_memory_retrievals_total",
            labels={"namespace": namespace, "tenant_scoped": str(tenant_scoped).lower()},
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
```

### Phase 3: Add `traverse_graph()` Method

**File:** `src/ultimate_discord_intelligence_bot/tools/graph_memory_tool.py`

**Estimated Lines:** ~100 lines

**Implementation:**

```python
def traverse_graph(
    self,
    *,
    graph_id: str,
    start_node: str,
    max_depth: int = 3,
    relation_filter: list[str] | None = None,
    namespace: str = "graph",
) -> StepResult:
    """Traverse graph from a starting node using BFS."""
    # First retrieve the graph
    graph_result = self.get_graph(graph_id=graph_id, namespace=namespace)
    if not graph_result.success:
        return graph_result
    
    nodes = graph_result.data["nodes"]
    edges = graph_result.data["edges"]
    
    # Build adjacency list
    adjacency: dict[str, list[dict]] = {}
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
                new_path = path + [neighbor]
                paths[neighbor] = new_path
                queue.append((neighbor, depth + 1, new_path))
    
    # Extract subgraph
    visited_nodes = [n for n in nodes if n.get("id") in visited]
    visited_edges = [
        e for e in edges
        if e.get("source") in visited and e.get("target") in visited
    ]
    
    self._metrics.counter(
        "graph_memory_traversals_total",
        labels={"namespace": namespace},
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
    )
```

### Phase 4: Add Helper Method `list_graphs()`

**File:** `src/ultimate_discord_intelligence_bot/tools/graph_memory_tool.py`

**Estimated Lines:** ~30 lines

**Implementation:**

```python
def list_graphs(
    self,
    *,
    namespace: str = "graph",
) -> StepResult:
    """List all graph IDs in a namespace."""
    namespace, tenant_scoped = self._resolve_namespace(namespace)
    ns_path = self._namespace_path(namespace)
    
    if not ns_path.exists():
        return StepResult.ok(graph_ids=[], count=0, namespace=namespace)
    
    graph_ids = [f.stem for f in ns_path.glob("*.json")]
    
    return StepResult.ok(
        graph_ids=graph_ids,
        count=len(graph_ids),
        namespace=namespace,
        tenant_scoped=tenant_scoped,
    )
```

---

## Metrics Instrumentation

**New Metrics:**

1. `graph_memory_searches_total{namespace, tenant_scoped}` - Counter
2. `graph_memory_retrievals_total{namespace, tenant_scoped}` - Counter
3. `graph_memory_traversals_total{namespace}` - Counter

**Existing Metrics (preserved):**

- `tool_runs_total{tool="graph_memory", outcome, tenant_scoped}`

---

## Testing Strategy

### Unit Tests (`tests/test_tools/test_graph_memory_tool.py`)

**Test Cases:**

1. **test_search_graphs_by_keywords**
   - Create 3 graphs with different keywords
   - Search for "AI" should return graphs with AI keywords
   - Verify scoring and ranking

2. **test_search_graphs_by_tags**
   - Create graphs with tags ["research", "production"]
   - Search by tag should filter correctly

3. **test_get_graph_existing**
   - Store a graph
   - Retrieve by ID
   - Verify all fields match

4. **test_get_graph_not_found**
   - Try to get non-existent graph
   - Should return StepResult.fail()

5. **test_traverse_graph_bfs**
   - Create graph with multiple paths
   - Traverse from start node
   - Verify BFS order and depth limits

6. **test_traverse_graph_relation_filter**
   - Create graph with multiple edge types
   - Filter by relation="mentions"
   - Verify only filtered edges followed

7. **test_list_graphs**
   - Create 5 graphs
   - List all
   - Verify count matches

8. **test_tenant_isolation**
   - Create graphs in different tenants
   - Search should only return tenant-scoped graphs

---

## Integration Points

### 1. CrewAI Tool Wrapper

**File:** `src/ultimate_discord_intelligence_bot/crewai_tool_wrappers.py`

Add wrapper for new query methods:

```python
class GraphMemoryQueryToolWrapper(CrewAIToolWrapper):
    """Wrapper for graph memory query operations."""
    
    @tool
    def search_knowledge_graphs(query: str, tags: list[str] = None) -> str:
        """Search stored knowledge graphs by keywords or tags."""
        tool = GraphMemoryTool()
        result = tool.search_graphs(query=query, tags=tags, limit=5)
        return json.dumps(result.to_dict())
    
    @tool
    def get_knowledge_graph(graph_id: str) -> str:
        """Retrieve a specific knowledge graph by ID."""
        tool = GraphMemoryTool()
        result = tool.get_graph(graph_id=graph_id)
        return json.dumps(result.to_dict())
```

### 2. Agent Configuration

**File:** `src/ultimate_discord_intelligence_bot/config/agents.yaml`

Add query tools to Knowledge Integration Steward:

```yaml
knowledge_integration_steward:
  # ... existing config ...
  tools:
    - graph_memory  # Existing (store)
    - graph_memory_query  # NEW (search/retrieve)
    - search_knowledge_graphs  # NEW (CrewAI wrapper)
    - get_knowledge_graph  # NEW (CrewAI wrapper)
```

---

## Benefits

### Immediate

1. **Enable Knowledge Retrieval** - Stored graphs become usable
2. **Support Context-Aware Analysis** - Agents can retrieve relevant past knowledge
3. **Cross-Session Intelligence** - Link insights across multiple analyses

### Medium-Term

1. **Semantic Search** - Find related content by concepts, not just keywords
2. **Relationship Discovery** - Identify connections between topics
3. **Knowledge Graph Visualization** - Export subgraphs for UI rendering

### Long-Term

1. **Graph Database Migration** - Query methods abstract storage (can migrate to Neo4j later)
2. **Advanced Analytics** - PageRank, centrality, community detection
3. **Multi-Tenant Knowledge Sharing** - Controlled cross-tenant graph access

---

## Implementation Checklist

- [ ] Add `search_graphs()` method (~80 lines)
- [ ] Add `get_graph()` method (~40 lines)
- [ ] Add `traverse_graph()` method (~100 lines)
- [ ] Add `list_graphs()` helper (~30 lines)
- [ ] Add new metrics (3 counters)
- [ ] Update `__all__` exports
- [ ] Create unit tests (8 test cases)
- [ ] Add CrewAI tool wrappers
- [ ] Update agent configuration
- [ ] Run `make test-fast` (validate)
- [ ] Run `make guards` (compliance)
- [ ] Update documentation

**Total Estimated:** ~250 lines of production code + ~200 lines of tests

---

## Next Steps

1. Implement all 4 methods in `graph_memory_tool.py`
2. Add comprehensive unit tests
3. Validate with `make test-fast` and `make guards`
4. Create completion document
5. Update progress report (11 of 12 fixes = 92%)

---

**Status:** Ready to implement  
**Priority:** MEDIUM  
**Estimated Time:** 1-2 hours  
**Dependencies:** None (all infrastructure exists)
