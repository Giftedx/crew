# MCP Server Integration Specification

## Overview

This document provides comprehensive documentation for all 12 MCP servers in the Ultimate Discord Intelligence Bot system and their integration patterns for Discord conversational AI.

## MCP Server Catalog

### 1. Main MCP Server (`server.py`)

**Purpose**: Core MCP server with basic utilities and composition hub

**Tools**:

- `health_check()` - Returns "ok" string for server health verification
- `echo(message, uppercase=false)` - Echo message back with optional uppercase
- `get_config_flag(name, default=None)` - Read configuration flags from environment/Settings

**Resources**:

- `settings://service_name` - Expose current service name

**Integration Points**:

- Mounts other MCP servers via feature flags
- Central entry point for Discord bot MCP communication
- Configuration management for all Discord AI features

### 2. CrewAI Server (`crewai_server.py`)

**Purpose**: Execute CrewAI crews and monitor agent performance

**Tools**:

- `list_available_crews()` - List available crew types and capabilities
- `get_crew_status()` - Get current crew system health and active executions
- `execute_crew(inputs, crew_type="default")` - Execute crew with provided inputs
- `get_agent_performance(agent_name=None)` - Get performance metrics for agents
- `abort_crew_execution(execution_id)` - Stop running crew execution

**Resources**:

- `crewai://agents` - List of available agents and their roles
- `crewai://tasks` - Available task types and dependencies
- `crewai://metrics/{execution_id}` - Detailed execution metrics

**Discord Integration**:

- Execute complex analytical queries via crew execution
- Monitor long-running analyses with progress updates
- Provide status information for Discord commands

### 3. Memory Server (`memory_server.py`)

**Purpose**: Vector search and namespace management for semantic memory

**Tools**:

- `vs_search(tenant, workspace, name, query, k=5, min_score=None)` - Vector similarity search
- `vs_list_namespaces(tenant, workspace)` - List available memory namespaces
- `vs_samples(tenant, workspace, name, probe="", n=3)` - Get sample payloads

**Resources**:

- `memory://{tenant}/{workspace}/{name}/stats` - Collection statistics

**Discord Integration**:

- Semantic search for conversation context
- Retrieve relevant memories for response generation
- Store conversation embeddings for personality evolution

### 4. Knowledge Graph Server (`kg_server.py`)

**Purpose**: Knowledge graph queries and policy resources

**Tools**:

- `kg_query(tenant, entity, depth=1)` - Get subgraph around entity
- `kg_timeline(tenant, entity)` - Get timeline events for entity
- `policy_keys_tool()` - List policy configuration keys

**Resources**:

- `policy://{key}` - Policy configuration by key
- `grounding://profiles` - Grounding configuration

**Discord Integration**:

- Entity relationship traversal for fact-checking
- Temporal reasoning for debate context
- Policy enforcement for content moderation

### 5. Routing Server (`routing_server.py`)

**Purpose**: Cost estimation and model routing optimization

**Tools**:

- `estimate_cost(model, input_tokens, output_tokens)` - Estimate USD cost for LLM calls
- `route_completion(task, tokens_hint=None)` - Suggest optimal model for task
- `choose_embedding_model(dimensions_required=None)` - Select embedding model

**Discord Integration**:

- Pre-flight cost estimation for expensive operations
- Dynamic model selection per message context
- Optimal embedding model selection for different content types

### 6. Creator Intelligence Server (`creator_intelligence_server.py`)

**Purpose**: Content ingestion and creator analytics

**Tools**:

- `ingest_youtube_video(url, tenant, workspace, fetch_transcript=true)` - Ingest YouTube content
- `ingest_twitch_clip(url, tenant, workspace)` - Ingest Twitch clips
- `query_creator_content(query_text, collection_type, tenant, workspace, limit, score_threshold)` - Search creator content
- `initialize_collections(tenant, workspace)` - Set up Vector DB collections
- `get_collection_stats(collection_type, tenant, workspace)` - Get collection statistics

**Resources**:

- `kg://schema` - Knowledge Graph schema definition

**Discord Integration**:

- Deep knowledge retrieval about tracked creators
- On-demand content ingestion from chat links
- Knowledge domain health metrics

### 7. Observability Server (`obs_server.py`)

**Purpose**: Metrics and system observability

**Tools**: (Implementation pending - placeholder for metrics tools)

**Discord Integration**:

- Discord-specific metrics (response time, decision accuracy)
- Personality drift tracking
- Conversation flow monitoring

### 8. Ingest Server (`ingest_server.py`)

**Purpose**: Multi-platform content ingestion

**Tools**: (Implementation pending - placeholder for ingestion tools)

**Discord Integration**:

- Process content links shared in Discord
- Bulk ingestion workflows
- Content monitoring and alerts

### 9. HTTP Server (`http_server.py`)

**Purpose**: HTTP utilities and web requests

**Tools**: (Implementation pending - placeholder for HTTP tools)

**Discord Integration**:

- External API calls for Discord webhooks
- Content fetching from shared URLs
- Rate limiting and retry logic

### 10. Agent-to-Agent Bridge Server (`a2a_bridge_server.py`)

**Purpose**: Agent-to-agent communication

**Tools**: (Implementation pending - placeholder for A2A tools)

**Discord Integration**:

- Multi-agent coordination for complex queries
- Agent handoff protocols
- Distributed processing workflows

### 11. Multimodal Server (`multimodal_server.py`)

**Purpose**: Multimodal content processing

**Tools**: (Implementation pending - placeholder for multimodal tools)

**Discord Integration**:

- Image analysis from Discord attachments
- Video content processing
- Audio transcription and analysis

## Integration Patterns

### 1. Discord Message Processing Flow

```
Discord Message → Main MCP Server → Route to Specialized Servers
    ↓
Memory Server (context retrieval)
    ↓
KG Server (entity resolution)
    ↓
Routing Server (model selection)
    ↓
CrewAI Server (complex analysis if needed)
    ↓
Response Generation → Memory Server (storage)
```

### 2. Personality Evolution Integration

```
User Interaction → Memory Server (store interaction)
    ↓
Reward Computation → Learning Engine
    ↓
Personality Update → Memory Server (store traits)
    ↓
Next Interaction → Personality Context → Response Generation
```

### 3. Content Analysis Integration

```
Discord Link → Creator Intelligence Server (ingest)
    ↓
CrewAI Server (analysis crew)
    ↓
KG Server (entity extraction)
    ↓
Memory Server (knowledge storage)
    ↓
Discord Response (analysis results)
```

## Configuration Flags

### Environment Variables for MCP Integration

```bash
# Core MCP Features
ENABLE_MCP_MEMORY=1
ENABLE_MCP_KG=1
ENABLE_MCP_CREWAI=1
ENABLE_MCP_ROUTER=1
ENABLE_MCP_CREATOR_INTELLIGENCE=1
ENABLE_MCP_OBS=1
ENABLE_MCP_INGEST=1
ENABLE_MCP_HTTP=1
ENABLE_MCP_A2A=1

# CrewAI Execution Control
ENABLE_MCP_CREWAI_EXECUTION=1

# Advanced Features
ENABLE_RL_CONTEXTUAL=1
ENABLE_RL_ADVANCED=1
```

## Error Handling

All MCP servers implement graceful degradation:

- Stub implementations when FastMCP not available
- Feature flag gating for optional servers
- Error boundaries to prevent cascade failures
- Fallback mechanisms for critical operations

## Performance Considerations

- Lazy loading of MCP server tools
- Caching of expensive operations (kg_query, vs_search)
- Rate limiting for external API calls
- Batch processing for multiple operations
- Async execution for non-blocking operations

## Security

- Read-only operations by default
- Execution capabilities gated behind feature flags
- Tenant isolation for multi-tenant deployments
- Input validation and sanitization
- Rate limiting and abuse prevention
