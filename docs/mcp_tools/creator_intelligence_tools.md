# Creator Intelligence MCP Tools

## Overview

The Creator Intelligence MCP tools provide TOS-compliant multi-platform content ingestion with automatic Knowledge Graph and Vector DB storage.

**Enable with:** `ENABLE_MCP_CREATOR_INTELLIGENCE=1`

## Available Tools

### 1. ingest_youtube_video

Fetch and store YouTube video with metadata and transcript.

**Parameters:**

- `url` (string, required): YouTube video URL
- `tenant` (string, default: "default"): Tenant identifier
- `workspace` (string, default: "main"): Workspace identifier
- `fetch_transcript` (boolean, default: true): Whether to fetch transcripts

**Returns:**

```json
{
  "platform": "youtube",
  "content_id": "dQw4w9WgXcQ",
  "content_type": "episode",
  "creator_id": "UC123abc",
  "title": "Never Gonna Give You Up",
  "url": "https://youtube.com/watch?v=dQw4w9WgXcQ",
  "published_at": "2009-10-25T06:57:33Z",
  "duration_seconds": 213,
  "has_transcript": true,
  "transcript_length": 1234,
  "stored_in_vector_db": true
}
```

**Example:**

```python
result = mcp.call_tool(
    "creator_ingest_youtube_video",
    {
        "url": "https://youtube.com/watch?v=example",
        "tenant": "h3podcast",
        "workspace": "production"
    }
)
```

---

### 2. ingest_twitch_clip

Fetch and store Twitch clip with metadata.

**Parameters:**

- `url` (string, required): Twitch clip URL
- `tenant` (string, default: "default"): Tenant identifier
- `workspace` (string, default: "main"): Workspace identifier

**Returns:**

```json
{
  "platform": "twitch",
  "content_id": "ABC123XYZ",
  "content_type": "clip",
  "creator_id": "hasanabi",
  "title": "Amazing Clip Title",
  "url": "https://clips.twitch.tv/ABC123XYZ",
  "published_at": "2025-01-17T12:00:00Z",
  "duration_seconds": 30,
  "stored_in_vector_db": true
}
```

---

### 3. query_creator_content

Search creator content using semantic similarity.

**Parameters:**

- `query_text` (string, required): Search query in natural language
- `collection_type` (string, default: "episodes"): episodes, segments, claims, quotes, topics
- `tenant` (string, default: "default"): Tenant identifier
- `workspace` (string, default: "main"): Workspace identifier
- `limit` (integer, default: 10): Maximum number of results
- `score_threshold` (float, default: 0.7): Minimum similarity score (0.0-1.0)

**Returns:**

```json
{
  "results": [
    {
      "id": "1",
      "payload": {
        "title": "Debate Episode Title",
        "platform": "youtube",
        "creator_id": "h3podcast"
      },
      "dense_score": 0.92,
      "hybrid_score": 0.89
    }
  ],
  "cache_hit": false,
  "result_count": 5
}
```

**Example:**

```python
result = mcp.call_tool(
    "creator_query_creator_content",
    {
        "query_text": "debate about artificial intelligence and ethics",
        "collection_type": "episodes",
        "tenant": "h3podcast",
        "limit": 5,
        "score_threshold": 0.8
    }
)
```

---

### 4. initialize_collections

Initialize all Creator Intelligence collections for a tenant/workspace.

**Parameters:**

- `tenant` (string, default: "default"): Tenant identifier
- `workspace` (string, default: "main"): Workspace identifier

**Returns:**

```json
{
  "initialized": [
    "default:main:creator_episodes",
    "default:main:creator_segments",
    "default:main:creator_claims",
    "default:main:creator_quotes",
    "default:main:creator_topics"
  ],
  "total": 5,
  "collections": ["episodes", "segments", "claims", "quotes", "topics"]
}
```

**Collections Created:**

- **creator_episodes** (768-dim): Full videos/episodes with platform metadata
- **creator_segments** (384-dim): Timestamped segments within episodes
- **creator_claims** (768-dim): Factual claims with verification status
- **creator_quotes** (384-dim): Notable quotes with speaker attribution
- **creator_topics** (768-dim): Topic embeddings for narrative tracking

---

### 5. get_collection_stats

Get statistics for a Creator Intelligence collection.

**Parameters:**

- `collection_type` (string, default: "episodes"): Collection type
- `tenant` (string, default: "default"): Tenant identifier
- `workspace` (string, default: "main"): Workspace identifier

**Returns:**

```json
{
  "collection_name": "default__main__creator_episodes",
  "vectors_count": 1234,
  "segments_count": 4,
  "disk_data_size": 52428800,
  "ram_data_size": 10485760,
  "config": {
    "distance": "cosine",
    "dimension": 768
  },
  "quantization_enabled": true,
  "sparse_vectors_enabled": true
}
```

---

## Available Resources

### kg://schema

Retrieve the Knowledge Graph schema definition.

**Example:**

```python
schema = mcp.read_resource("kg://schema")
print(schema)  # Returns YAML schema definition
```

---

## Usage Workflow

### 1. Initialize Collections

Before ingesting content, initialize collections for your tenant/workspace:

```python
# Initialize collections
init_result = mcp.call_tool(
    "creator_initialize_collections",
    {
        "tenant": "h3podcast",
        "workspace": "production"
    }
)
```

### 2. Ingest Content

Ingest content from multiple platforms:

```python
# YouTube video
youtube_result = mcp.call_tool(
    "creator_ingest_youtube_video",
    {
        "url": "https://youtube.com/watch?v=example",
        "tenant": "h3podcast",
        "fetch_transcript": True
    }
)

# Twitch clip
twitch_result = mcp.call_tool(
    "creator_ingest_twitch_clip",
    {
        "url": "https://clips.twitch.tv/example",
        "tenant": "hasanabi"
    }
)
```

### 3. Query Ingested Content

Search using semantic similarity:

```python
search_result = mcp.call_tool(
    "creator_query_creator_content",
    {
        "query_text": "political debate about healthcare",
        "collection_type": "episodes",
        "tenant": "h3podcast",
        "limit": 10,
        "score_threshold": 0.75
    }
)

for item in search_result["results"]:
    print(f"Title: {item['payload']['title']}")
    print(f"Score: {item['dense_score']:.2f}")
```

### 4. Monitor Collection Health

Check collection statistics:

```python
stats = mcp.call_tool(
    "creator_get_collection_stats",
    {
        "collection_type": "episodes",
        "tenant": "h3podcast"
    }
)

print(f"Total vectors: {stats['vectors_count']}")
print(f"Quantization: {'enabled' if stats['quantization_enabled'] else 'disabled'}")
```

---

## Advanced Features

### Semantic Caching

The system automatically caches query results. When you query with a vector similar to a previous query (similarity > 0.95), cached results are returned instantly:

- **Cache Hit Latency:** <10ms
- **Cache Miss Latency:** <200ms
- **Cache TTL:** 1 hour (configurable)
- **Expected Hit Rate:** >80% for repeat queries

### Multi-Modal RAG

Ingested content includes rich metadata payloads that support retrieval-augmented generation:

- Platform metadata (views, likes, comments)
- Temporal information (timestamps, durations)
- Creator attribution (channel, streamer)
- Full transcript text
- Content embeddings

### Tenant Isolation

All data is isolated by tenant and workspace:

- Collections: `{tenant}:{workspace}:{collection_name}`
- Queries: Automatic tenant filtering
- No cross-tenant data leakage

---

## Error Handling

All tools return StepResult-compatible responses:

**Success:**

```json
{
  "status": "success",
  "data": { ... }
}
```

**Failure:**

```json
{
  "status": "retryable",  // or "bad_request", "rate_limited", etc.
  "error": "Descriptive error message"
}
```

Common error statuses:

- `bad_request`: Invalid input, don't retry
- `retryable`: Temporary error, safe to retry
- `rate_limited`: API rate limit hit, backoff and retry
- `not_implemented`: Feature not yet implemented

---

## Configuration

### Environment Variables

```bash
# Enable Creator Intelligence MCP tools
ENABLE_MCP_CREATOR_INTELLIGENCE=1

# Qdrant Vector DB
QDRANT_URL=http://localhost:6333
QDRANT_API_KEY=your-api-key  # Optional

# OpenAI (for quality embeddings)
OPENAI_API_KEY=sk-your-key  # Optional, falls back to local models

# Feature toggles
ENABLE_MEMORY_OPTIMIZATIONS=1  # Enable advanced caching
```

### Collection Configuration

Collections are pre-configured with optimal settings in `memory/creator_intelligence_collections.py`:

- **INT8 Quantization:** 75% memory reduction
- **HNSW Indexing:** Fast approximate nearest neighbor
- **Payload Indexes:** Fast filtering on tenant/workspace/platform
- **Hybrid Search:** Dense + sparse vectors for better recall

---

## Performance Characteristics

| Operation | Latency | Throughput |
|-----------|---------|------------|
| Ingest YouTube video (no transcript) | <2s | 30/min |
| Ingest YouTube video (with transcript) | <5s | 12/min |
| Query with cache hit | <10ms | 10,000/min |
| Query with cache miss | <200ms | 300/min |
| Collection initialization | <1s | N/A |

---

## Testing

Run tests for Creator Intelligence tools:

```bash
# Unit tests
pytest tests/test_creator_intelligence_ingestion.py -v
pytest tests/test_embedding_service.py -v
pytest tests/test_creator_intelligence_collections.py -v

# Integration test with actual YouTube video (requires network)
python -m scripts.test_creator_intelligence_ingestion
```

---

## Troubleshooting

### Issue: "sentence-transformers not available"

**Solution:** Install optional dependencies:

```bash
pip install sentence-transformers torch
```

### Issue: "Qdrant connection failed"

**Solution:** Verify Qdrant is running:

```bash
docker-compose up -d qdrant
curl http://localhost:6333/health
```

### Issue: "Collection not found"

**Solution:** Initialize collections first:

```bash
python -m scripts.init_creator_collections --tenant your_tenant --workspace your_workspace --verify
```

---

## Next Steps

After setting up Creator Intelligence tools, consider:

1. **Enable Batch Ingestion:** Implement YouTube Data API for channel-wide ingestion
2. **Add More Platforms:** Twitter/X, TikTok, Reddit
3. **Build Feature Agents:** Smart Clip Composer, Narrative Tracker
4. **Deploy MoE Routing:** Intelligent model selection for cost optimization

See the [Master Plan](../../understand-cursor-rules.plan.md) for detailed roadmap.
