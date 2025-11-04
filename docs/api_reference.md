# HTTP API Reference (FastAPI)

This document catalogs the HTTP endpoints exposed by the service in `src/server/app.py`. Endpoints are registered via small route modules and many are gated by feature flags. Paths below are relative to the service base URL (default <http://localhost:8000>).

- App factory: `src/server/app.py::create_app`
- Route registrars: `src/server/routes/`

## Authentication

- Most endpoints are open by default for local development.
- A2A JSON-RPC can be protected by API key headers when enabled:
  - Flags: `ENABLE_A2A_API_KEY=1` and `A2A_API_KEY="k1,k2,..."`
  - Header: `X-API-Key: <key>`

## Rate limiting

- Optional fixed-window limiter (1s window) applied to all endpoints except `/health` and `/metrics`.
- Flags: `ENABLE_RATE_LIMITING=1`, `RATE_LIMIT_BURST` (or `RATE_LIMIT_RPS`, default 10)
- Implementation: `src/server/rate_limit.py`

## Tenancy headers

Some endpoints and tools respect tenant scoping via headers:

- `X-Tenant-Id: <tenant>`
- `X-Workspace-Id: <workspace>`

Where not provided, defaults may be used (`tenant=default`, `workspace=main`).

---

## Core endpoints

### GET /health

Simple service health. Always available.

### GET /activities/health

Lightweight health for Discord Activities local dev. Always available.

### GET /metrics  (conditional)

Prometheus exposition endpoint.

- Flag: `ENABLE_PROMETHEUS_ENDPOINT=1`
- Optional path override: `prometheus_endpoint_path` in settings
- Source: `src/server/routes/metrics.py`

### GET /activities/echo  (conditional)

Request echo for client debugging (method, path, selected headers, client).

- Flag: `ENABLE_ACTIVITIES_ECHO=1` (or settings.enable_activities_echo)
- Source: `src/server/routes/activities.py`

---

## A2A JSON-RPC Adapter  (conditional)

Expose selected tools over JSON-RPC 2.0.

- Flags: `ENABLE_A2A_API=1` to enable router; optional `ENABLE_A2A_API_KEY=1` + `A2A_API_KEY` for auth
- Module: `src/server/a2a_router.py`, registrars in `src/server/routes/a2a.py`

Endpoints:

- POST `/a2a/jsonrpc` — JSON-RPC 2.0 (single or batch)
- GET `/a2a/agent-card` — Agent card and capabilities
- GET `/a2a/skills` — Enabled skills with input schemas

JSON-RPC errors use standard codes: -32600 (Invalid Request), -32601 (Method not found), -32602 (Invalid params), -32603 (Internal error).

See `docs/a2a_api.md` for method list, schemas, and examples.

---

## Content Pipeline API  (conditional)

Run the unified ContentPipeline and manage async jobs.

- Flags in settings: `enable_pipeline_run_api`, `enable_pipeline_job_queue`
- Module: `src/server/routes/pipeline_api.py`

Endpoints:

- POST `/pipeline/run`
  - Body: `{ "url": string, "quality": string? , "tenant_id"?: string, "workspace_id"?: string }`
  - 200 on success (payload mirrors `StepResult.to_dict()`), 4xx/5xx on error.
- POST `/pipeline/jobs`  (requires job queue flag)
  - Body: `{ "url": string, "quality"?: string, "tenant_id"?: string, "workspace_id"?: string }`
  - 201 with job object `{id,status,tenant_id,workspace_id,...}`
- GET `/pipeline/jobs/{job_id}` — Retrieve job status/result
- DELETE `/pipeline/jobs/{job_id}` — Cancel/delete job
- GET `/pipeline/jobs` — List jobs (optional query: `tenant_id`, `workspace_id`, `status`)

Notes:

- Jobs execute in background with periodic cleanup.
- Tenancy is stored on each job and returned in responses.

---

## Autonomous Intelligence API  (conditional)

Programmatic trigger for the autonomous intelligence workflow (non-Discord).

- Flag: `enable_autointel_api` in settings
- Module: `src/server/routes/autointel.py`

Endpoint:

- POST `/autointel`
  - Body: `{ "url": string, "depth"?: "standard|deep|comprehensive|experimental", "tenant_id"?: string, "workspace_id"?: string }`
  - 200 on success with `{success: true, data: {...}}` or 500 on failure with error details.

---

## Performance Dashboard API

Dashboard REST API and static UI.

- Modules: `src/server/routers/performance_dashboard.py` (API), `src/server/routes/performance_dashboard.py` (mount)

Endpoints (prefix `/api/performance`):

- GET `/` — Full dashboard data
- GET `/metrics/summary` — Overall metrics summary
- GET `/content-types` — Breakdown by content type
- GET `/checkpoints` — Early exit checkpoint analytics
- GET `/quality-trends` — Quality metrics trend (query: `hours`)
- POST `/record` — Record pipeline outcome (see function docstring for fields)
- DELETE `/reset` — Reset metrics (for testing only)

Static dashboard:

- GET `/dashboard` — Serves HTML page from `src/server/static/performance_dashboard.html`

---

## Pilot API  (conditional)

Experimental LangGraph pilot

- Flag: `ENABLE_LANGGRAPH_PILOT_API=1` (or settings.enable_langgraph_pilot_api)
- Endpoint: GET `/pilot/run` (optional query: `tenant`, `workspace`, `enable_segment`, `enable_embed`)
- Module: `src/server/routes/pilot.py`

---

## Archive & Alerts Routers  (optional/external)

---

## Implementation Verification

**Last Verified**: November 3, 2025
**Server Factory**: `src/server/app.py::create_app` (122 lines)
**Route Modules**: `src/server/routes/` (10+ registration functions)

**Registered Routers** (verified from `create_app`):

1. Archive routes (`register_archive_routes`)
2. Alert routes (`register_alert_routes`)
3. A2A router (`register_a2a_router`) - Feature-gated
4. Pipeline routes (`register_pipeline_routes`) - Feature-gated
5. Autonomous Intelligence routes (`register_autointel_routes`) - Feature-gated
6. Performance dashboard (`register_performance_dashboard`)
7. Metrics endpoint (`register_metrics_endpoint`) - Feature-gated
8. Pilot route (`register_pilot_route`) - Feature-gated
9. Health routes (`register_health_routes`)
10. Activities echo (`register_activities_echo`) - Feature-gated

**Middleware Stack** (in registration order):

- CORS middleware (conditional)
- Metrics middleware (conditional)
- API cache middleware (conditional)
- Rate limit middleware (conditional)

**Lifespan Hooks**:

- Tracing initialization (conditional)
- Enhanced monitoring system startup/shutdown
- Logfire setup (conditional)
- Qdrant client pre-initialization (lazy)

**Feature Flags** (primary):

- `ENABLE_A2A_API` - A2A JSON-RPC adapter
- `ENABLE_PROMETHEUS_ENDPOINT` - Metrics endpoint
- `ENABLE_RATE_LIMITING` - Rate limiting middleware
- `ENABLE_TRACING` - OpenTelemetry tracing
- `ENABLE_CORS` - CORS middleware
- `enable_pipeline_run_api` - Pipeline execution API
- `enable_autointel_api` - Autonomous intelligence API
- `enable_langgraph_pilot_api` - LangGraph pilot

These routers are included only if their modules are importable.

- Archive: `archive.discord_store.api.api_router` → mounted router (paths under project-specific prefix)
- Alerts: `ops.alert_adapter.alert_router` → mounted router

---

## Error shape (non-JSON-RPC)

Many endpoints return a structured `StepResult` in their payloads when calling internal tools.
Typical HTTP error responses follow FastAPI conventions with appropriate 4xx/5xx status codes and `detail` messages.

---

## Examples

cURL — pipeline run:

```bash
curl -sS -X POST http://localhost:8000/pipeline/run \
    -H 'Content-Type: application/json' \
    -d '{"url": "https://youtube.com/watch?v=...", "quality": "1080p", "tenant_id": "default", "workspace_id": "main"}'
```

cURL — A2A JSON-RPC (single):

```bash
curl -sS -X POST http://localhost:8000/a2a/jsonrpc \
    -H 'Content-Type: application/json' \
    -H 'X-API-Key: key1' \
    -d '{"jsonrpc":"2.0","id":"1","method":"tools.text_analyze","params":{"text":"hello world"}}'
```

---

Last Updated: November 3, 2025
Status: Current — verified against `src/server/routes/*`
Related: [A2A API](a2a_api.md), [MCP Server](mcp.md)

**Base Class:** `MemoryService`
**File:** `src/ultimate_discord_intelligence_bot/services/memory_service.py`

#### Methods

##### `store_content(content: str, tenant: str, workspace: str) -> StepResult`

Stores content in the memory system with tenant isolation.

**Parameters:**

- `content` (str): Content to store
- `tenant` (str): Tenant identifier for isolation
- `workspace` (str): Workspace identifier

**Returns:**

- `StepResult`: Success/failure result with stored content ID

**Example:**

```python
from ultimate_discord_intelligence_bot.services.memory_service import MemoryService

memory_service = MemoryService()
result = memory_service.store_content(
    content="Important analysis data",
    tenant="tenant_123",
    workspace="project_x"
)

if result.success:
    print(f"Stored with ID: {result.data['id']}")
```

##### `retrieve_content(query: str, tenant: str, workspace: str) -> StepResult`

Retrieves content from memory based on semantic similarity.

**Parameters:**

- `query` (str): Search query
- `tenant` (str): Tenant identifier
- `workspace` (str): Workspace identifier

**Returns:**

- `StepResult`: Retrieved content with relevance scores

##### `update_content(content_id: str, new_content: str, tenant: str, workspace: str) -> StepResult`

Updates existing content in memory.

**Parameters:**

- `content_id` (str): ID of content to update
- `new_content` (str): New content
- `tenant` (str): Tenant identifier
- `workspace` (str): Workspace identifier

**Returns:**

- `StepResult`: Update success/failure result

##### `delete_content(content_id: str, tenant: str, workspace: str) -> StepResult`

Deletes content from memory.

**Parameters:**

- `content_id` (str): ID of content to delete
- `tenant` (str): Tenant identifier
- `workspace` (str): Workspace identifier

**Returns:**

- `StepResult`: Deletion success/failure result

### Prompt Engine Service

**Base Class:** `PromptEngine`
**File:** `src/ultimate_discord_intelligence_bot/services/prompt_engine.py`

#### Methods

##### `generate_prompt(template: str, context: dict) -> StepResult`

Generates prompts from templates with context substitution.

**Parameters:**

- `template` (str): Prompt template with placeholders
- `context` (dict): Context variables for substitution

**Returns:**

- `StepResult`: Generated prompt

**Example:**

```python
from ultimate_discord_intelligence_bot.services.prompt_engine import PromptEngine

prompt_engine = PromptEngine()
result = prompt_engine.generate_prompt(
    template="Analyze this content: {content} for {analysis_type}",
    context={"content": "Sample text", "analysis_type": "bias detection"}
)

if result.success:
    print(f"Generated prompt: {result.data}")
```

##### `optimize_prompt(prompt: str, optimization_target: str = "accuracy") -> StepResult`

Optimizes prompts for better performance.

**Parameters:**

- `prompt` (str): Original prompt
- `optimization_target` (str): Optimization target (accuracy, speed, cost)

**Returns:**

- `StepResult`: Optimized prompt

##### `validate_prompt(prompt: str) -> StepResult`

Validates prompt format and content.

**Parameters:**

- `prompt` (str): Prompt to validate

**Returns:**

- `StepResult`: Validation result with suggestions

### OpenRouter Service

**Base Class:** `OpenRouterService`
**File:** `src/ultimate_discord_intelligence_bot/services/openrouter_service.py`

#### Methods

##### `generate_response(messages: list, model: str = None) -> StepResult`

Generates responses using OpenRouter API.

**Parameters:**

- `messages` (list): List of message objects
- `model` (str): Model to use (optional, uses default if not specified)

**Returns:**

- `StepResult`: Generated response

**Example:**

```python
from ultimate_discord_intelligence_bot.services.openrouter_service import OpenRouterService

openrouter_service = OpenRouterService()
messages = [
    {"role": "user", "content": "Analyze this text for logical fallacies"}
]

result = openrouter_service.generate_response(messages)
if result.success:
    print(f"Response: {result.data}")
```

##### `get_available_models() -> StepResult`

Retrieves list of available models.

**Returns:**

- `StepResult`: List of available models with metadata

##### `get_model_info(model_name: str) -> StepResult`

Gets detailed information about a specific model.

**Parameters:**

- `model_name` (str): Name of the model

**Returns:**

- `StepResult`: Model information including capabilities and pricing

## Tool APIs

### Base Tool Interface

All tools inherit from `BaseTool` and implement the following interface:

#### `_run(*args, **kwargs) -> StepResult`

Main execution method for all tools.

**Returns:**

- `StepResult`: Tool execution result with data or error information

### Content Analysis Tools

#### Logical Fallacy Tool

**Class:** `LogicalFallacyTool`
**File:** `src/ultimate_discord_intelligence_bot/tools/logical_fallacy_tool.py`

##### `_run(text: str) -> StepResult`

Detects logical fallacies in text.

**Parameters:**

- `text` (str): Text to analyze

**Returns:**

- `StepResult`: Detected fallacies with confidence scores

**Example:**

```python
from ultimate_discord_intelligence_bot.tools.logical_fallacy_tool import LogicalFallacyTool

tool = LogicalFallacyTool()
result = tool._run("Everyone knows this is true, so you must agree.")

if result.success:
    fallacies = result.data.get('fallacies', [])
    for fallacy in fallacies:
        print(f"Fallacy: {fallacy['type']}, Confidence: {fallacy['confidence']}")
```

#### Claim Extractor Tool

**Class:** `ClaimExtractorTool`
**File:** `src/ultimate_discord_intelligence_bot/tools/claim_extractor_tool.py`

##### `_run(text: str) -> StepResult`

Extracts factual claims from text.

**Parameters:**

- `text` (str): Text to analyze

**Returns:**

- `StepResult`: Extracted claims with metadata

#### Sentiment Tool

**Class:** `SentimentTool`
**File:** `src/ultimate_discord_intelligence_bot/tools/sentiment_tool.py`

##### `_run(text: str) -> StepResult`

Analyzes sentiment in text.

**Parameters:**

- `text` (str): Text to analyze

**Returns:**

- `StepResult`: Sentiment analysis with scores

### Media Processing Tools

#### Multi-Platform Download Tool

**Class:** `MultiPlatformDownloadTool`
**File:** `src/ultimate_discord_intelligence_bot/tools/multi_platform_download_tool.py`

##### `_run(url: str, quality: str = "720p") -> StepResult`

Downloads content from multiple platforms.

**Parameters:**

- `url` (str): URL to download
- `quality` (str): Quality preference

**Returns:**

- `StepResult`: Download result with file path

**Example:**

```python
from ultimate_discord_intelligence_bot.tools.multi_platform_download_tool import MultiPlatformDownloadTool

tool = MultiPlatformDownloadTool()
result = tool._run("https://youtube.com/watch?v=example", quality="1080p")

if result.success:
    print(f"Downloaded to: {result.data['file_path']}")
```

#### Audio Transcription Tool

**Class:** `AudioTranscriptionTool`
**File:** `src/ultimate_discord_intelligence_bot/tools/audio_transcription_tool.py`

##### `_run(audio_file_path: str) -> StepResult`

Transcribes audio to text.

**Parameters:**

- `audio_file_path` (str): Path to audio file

**Returns:**

- `StepResult`: Transcription result

### Discord Integration Tools

#### Discord Post Tool

**Class:** `DiscordPostTool`
**File:** `src/ultimate_discord_intelligence_bot/tools/discord_post_tool.py`

##### `_run(webhook_url: str, content: str, embeds: list = None) -> StepResult`

Posts messages to Discord channels.

**Parameters:**

- `webhook_url` (str): Discord webhook URL
- `content` (str): Message content
- `embeds` (list): Discord embeds (optional)

**Returns:**

- `StepResult`: Post result

**Example:**

```python
from ultimate_discord_intelligence_bot.tools.discord_post_tool import DiscordPostTool

tool = DiscordPostTool()
result = tool._run(
    webhook_url="https://discord.com/api/webhooks/...",
    content="Analysis complete!",
    embeds=[{"title": "Results", "description": "Analysis results here"}]
)

if result.success:
    print("Message posted successfully")
```

### Search & Retrieval Tools

#### Vector Search Tool

**Class:** `VectorSearchTool`
**File:** `src/ultimate_discord_intelligence_bot/tools/vector_search_tool.py`

##### `_run(query: str, limit: int = 10) -> StepResult`

Performs semantic search using vector embeddings.

**Parameters:**

- `query` (str): Search query
- `limit` (int): Maximum number of results

**Returns:**

- `StepResult`: Search results with relevance scores

#### Fact Check Tool

**Class:** `FactCheckTool`
**File:** `src/ultimate_discord_intelligence_bot/tools/fact_check_tool.py`

##### `_run(claim: str, sources: list = None) -> StepResult`

Performs fact-checking on claims.

**Parameters:**

- `claim` (str): Claim to verify
- `sources` (list): Optional source list

**Returns:**

- `StepResult`: Fact-check results with verification status

## Configuration API

### Settings Management

**Class:** `Settings`
**File:** `src/ultimate_discord_intelligence_bot/settings.py`

#### Environment Variables

The system uses environment variables for configuration:

```bash
# Core API Keys
OPENROUTER_API_KEY=your_openrouter_key
SERPER_API_KEY=your_serper_key
ANTHROPIC_API_KEY=your_anthropic_key

# Feature Flags
ENABLE_UNIFIED_KNOWLEDGE=true
ENABLE_DEBATE_ANALYSIS=true
ENABLE_FACT_CHECKING=true

# System Configuration
LOG_LEVEL=INFO
DATABASE_URL=sqlite:///./ultimate_discord_intelligence_bot.db
CACHE_TTL_SECONDS=3600
MAX_RETRIES=5
RETRY_DELAY_SECONDS=2

# MCP Configuration
MCP_CLIENT_TIMEOUT=30
MCP_RESOURCE_LIMIT=100
MCP_CALL_CONCURRENCY=5

# Memory Configuration
MEM0_API_KEY=your_mem0_key
MEM0_USER_ID=your_user_id
MEM0_AGENT_ID=your_agent_id
```

#### Configuration Access

```python
from ultimate_discord_intelligence_bot.settings import get_settings

settings = get_settings()
print(f"Log level: {settings.LOG_LEVEL}")
print(f"Database URL: {settings.DATABASE_URL}")
```

## Error Handling

### StepResult Format

All API methods return `StepResult` objects with the following structure:

```python
class StepResult:
    def __init__(self, success: bool, data: Any = None, error: str = None, status: str = "success"):
        self.success = success
        self.data = data
        self.error = error
        self.status = status
```

#### Success Response

```python
{
    "success": True,
    "data": {
        "id": "result_123",
        "content": "Analysis results",
        "metadata": {...}
    },
    "error": None,
    "status": "success"
}
```

#### Error Response

```python
{
    "success": False,
    "data": None,
    "error": "Detailed error message",
    "status": "error"
}
```

### Error Types

- **ValidationError**: Input validation failures
- **AuthenticationError**: API key or authentication issues
- **RateLimitError**: Rate limit exceeded
- **ServiceUnavailableError**: External service unavailable
- **InternalError**: Internal system errors

## Rate Limiting

### OpenRouter API Limits

- **Requests per minute**: Varies by model
- **Tokens per minute**: Model-specific limits
- **Concurrent requests**: 5 (configurable)

### Retry Logic

Automatic retry with exponential backoff:

- **Max retries**: 5 (configurable)
- **Base delay**: 2 seconds (configurable)
- **Backoff multiplier**: 2x
- **Max delay**: 60 seconds

## Authentication

### API Key Management

API keys are managed through environment variables:

```python
import os

# Check if API key is available
if not os.getenv("OPENROUTER_API_KEY"):
    raise ValueError("OPENROUTER_API_KEY environment variable not set")
```

### Security Best Practices

- Store API keys in environment variables
- Use different keys for different environments
- Rotate keys regularly
- Monitor API key usage
- Implement proper access controls

## Monitoring & Observability

### Metrics Collection

The system collects various metrics:

- **Request counts**: Total API requests
- **Response times**: API response latency
- **Error rates**: Failed request percentages
- **Resource usage**: Memory and CPU utilization

### Logging

Structured logging with different levels:

```python
import logging

logger = logging.getLogger(__name__)
logger.info("Processing request", extra={
    "tenant": "tenant_123",
    "workspace": "project_x",
    "request_id": "req_456"
})
```

### Health Checks

Health check endpoints for monitoring:

- **Service health**: `/health`
- **Database connectivity**: `/health/db`
- **External services**: `/health/external`

## Best Practices

### API Usage

1. **Always check StepResult.success** before accessing data
2. **Handle errors gracefully** with appropriate fallbacks
3. **Use appropriate timeouts** for external API calls
4. **Implement retry logic** for transient failures
5. **Monitor rate limits** and implement backoff

### Performance Optimization

1. **Use caching** for frequently accessed data
2. **Batch requests** when possible
3. **Optimize payload sizes** to reduce bandwidth
4. **Use connection pooling** for database connections
5. **Implement proper indexing** for search operations

### Security Considerations

1. **Validate all inputs** before processing
2. **Sanitize outputs** before returning to clients
3. **Use HTTPS** for all external communications
4. **Implement proper authentication** and authorization
5. **Monitor for suspicious activity** and implement alerts

---
