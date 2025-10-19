# API Reference - Unified System

## Overview

This document provides comprehensive API reference for all unified system components, including endpoints, parameters, responses, and usage examples.

## Knowledge Layer API

### UnifiedMemoryService

#### `store_content`

Store content in the unified memory system.

**Parameters:**

- `content` (str): The content to store
- `tenant_id` (str): Tenant identifier
- `workspace_id` (str): Workspace identifier
- `metadata` (dict, optional): Additional metadata
- `embeddings` (list, optional): Pre-computed embeddings

**Response:**

```python
StepResult(
    success=True,
    data={
        "content_id": "uuid-string",
        "stored_at": "2024-01-01T00:00:00Z",
        "metadata": {...}
    }
)
```

**Example:**

```python
result = await memory_service.store_content(
    content="Sample content",
    tenant_id="tenant_1",
    workspace_id="workspace_1",
    metadata={"source": "api", "type": "document"}
)
```

#### `retrieve_content`

Retrieve content from the unified memory system.

**Parameters:**

- `query` (str): Search query
- `tenant_id` (str): Tenant identifier
- `workspace_id` (str): Workspace identifier
- `limit` (int, optional): Maximum number of results (default: 10)
- `filters` (dict, optional): Additional filters

**Response:**

```python
StepResult(
    success=True,
    data=[
        {
            "content_id": "uuid-string",
            "content": "Retrieved content",
            "score": 0.95,
            "metadata": {...}
        }
    ]
)
```

### UnifiedRetrievalEngine

#### `retrieve_content`

Advanced content retrieval with multi-source ranking.

**Parameters:**

- `query` (str): Search query
- `tenant_id` (str): Tenant identifier
- `workspace_id` (str): Workspace identifier
- `limit` (int, optional): Maximum number of results
- `ranking_strategy` (str, optional): Ranking strategy to use

**Response:**

```python
StepResult(
    success=True,
    data=[
        {
            "content_id": "uuid-string",
            "content": "Retrieved content",
            "score": 0.95,
            "source": "vector_store",
            "metadata": {...}
        }
    ]
)
```

### UnifiedContextBuilder

#### `build_context`

Build comprehensive context for agents.

**Parameters:**

- `agent_id` (str): Agent identifier
- `agent_type` (str): Agent type
- `query` (str): Context query
- `tenant_id` (str): Tenant identifier
- `workspace_id` (str): Workspace identifier
- `max_context_length` (int, optional): Maximum context length

**Response:**

```python
StepResult(
    success=True,
    data={
        "context": "Comprehensive context string",
        "sources": [...],
        "metadata": {...}
    }
)
```

## Router System API

### UnifiedRouterService

#### `route_request`

Route requests to the best available LLM provider.

**Parameters:**

- `prompt` (str): The prompt to route
- `tenant_id` (str): Tenant identifier
- `workspace_id` (str): Workspace identifier
- `max_tokens` (int, optional): Maximum tokens
- `temperature` (float, optional): Temperature setting

**Response:**

```python
StepResult(
    success=True,
    data={
        "model": "gpt-4",
        "provider": "openai",
        "response": "Generated response",
        "tokens": 150,
        "cost": 0.001
    }
)
```

### UnifiedCostTracker

#### `record_usage`

Record usage for cost tracking.

**Parameters:**

- `tenant_id` (str): Tenant identifier
- `workspace_id` (str): Workspace identifier
- `model` (str): Model used
- `provider` (str): Provider used
- `input_tokens` (int): Input tokens
- `output_tokens` (int): Output tokens
- `cost` (float): Cost incurred

**Response:**

```python
StepResult(
    success=True,
    data={
        "usage_id": "uuid-string",
        "recorded_at": "2024-01-01T00:00:00Z"
    }
)
```

#### `get_usage_summary`

Get usage summary for a tenant.

**Parameters:**

- `tenant_id` (str): Tenant identifier
- `workspace_id` (str, optional): Workspace identifier
- `start_date` (str, optional): Start date (ISO format)
- `end_date` (str, optional): End date (ISO format)

**Response:**

```python
StepResult(
    success=True,
    data={
        "total_cost": 10.50,
        "total_tokens": 50000,
        "usage_by_model": {...},
        "usage_by_provider": {...}
    }
)
```

## Cache System API

### UnifiedCacheService

#### `store`

Store data in the unified cache system.

**Parameters:**

- `key` (str): Cache key
- `value` (any): Value to cache
- `tenant_id` (str): Tenant identifier
- `workspace_id` (str): Workspace identifier
- `ttl` (int, optional): Time to live in seconds

**Response:**

```python
StepResult(
    success=True,
    data={
        "key": "cache_key",
        "stored_at": "2024-01-01T00:00:00Z",
        "ttl": 3600
    }
)
```

#### `get`

Retrieve data from the unified cache system.

**Parameters:**

- `key` (str): Cache key
- `tenant_id` (str): Tenant identifier
- `workspace_id` (str): Workspace identifier

**Response:**

```python
StepResult(
    success=True,
    data={
        "value": "cached_value",
        "retrieved_at": "2024-01-01T00:00:00Z",
        "ttl_remaining": 1800
    }
)
```

#### `delete`

Delete data from the unified cache system.

**Parameters:**

- `key` (str): Cache key
- `tenant_id` (str): Tenant identifier
- `workspace_id` (str): Workspace identifier

**Response:**

```python
StepResult(
    success=True,
    data={
        "key": "cache_key",
        "deleted_at": "2024-01-01T00:00:00Z"
    }
)
```

### CacheOptimizer

#### `optimize_ttl`

Optimize TTL for cache entries.

**Parameters:**

- `key` (str): Cache key
- `tenant_id` (str): Tenant identifier
- `workspace_id` (str): Workspace identifier
- `access_pattern` (str, optional): Access pattern analysis

**Response:**

```python
StepResult(
    success=True,
    data={
        "key": "cache_key",
        "optimized_ttl": 7200,
        "confidence": 0.85
    }
)
```

## Orchestration System API

### UnifiedOrchestrationService

#### `submit_task`

Submit a task for orchestration.

**Parameters:**

- `task_type` (str): Type of task
- `payload` (dict): Task payload
- `tenant_id` (str): Tenant identifier
- `workspace_id` (str): Workspace identifier
- `priority` (str, optional): Task priority

**Response:**

```python
StepResult(
    success=True,
    data={
        "task_id": "uuid-string",
        "status": "pending",
        "submitted_at": "2024-01-01T00:00:00Z"
    }
)
```

#### `get_task_status`

Get the status of a task.

**Parameters:**

- `task_id` (str): Task identifier
- `tenant_id` (str): Tenant identifier
- `workspace_id` (str): Workspace identifier

**Response:**

```python
StepResult(
    success=True,
    data={
        "task_id": "uuid-string",
        "status": "completed",
        "result": {...},
        "started_at": "2024-01-01T00:00:00Z",
        "completed_at": "2024-01-01T00:05:00Z"
    }
)
```

### TaskManager

#### `get_tasks`

Get tasks for a tenant.

**Parameters:**

- `tenant_id` (str): Tenant identifier
- `workspace_id` (str, optional): Workspace identifier
- `status` (str, optional): Filter by status
- `limit` (int, optional): Maximum number of tasks

**Response:**

```python
StepResult(
    success=True,
    data=[
        {
            "task_id": "uuid-string",
            "task_type": "analysis",
            "status": "completed",
            "created_at": "2024-01-01T00:00:00Z"
        }
    ]
)
```

## Agent Bridge API

### AgentBridge

#### `share_insight`

Share an insight between agents.

**Parameters:**

- `agent_id` (str): Agent identifier
- `agent_type` (str): Agent type
- `insight_type` (str): Type of insight
- `title` (str): Insight title
- `description` (str): Insight description
- `context` (dict, optional): Additional context
- `tags` (list, optional): Tags for categorization
- `confidence_score` (float, optional): Confidence score
- `priority` (str, optional): Priority level

**Response:**

```python
StepResult(
    success=True,
    data={
        "insight_id": "uuid-string",
        "shared_at": "2024-01-01T00:00:00Z",
        "recipients": [...]
    }
)
```

#### `request_insights`

Request insights from other agents.

**Parameters:**

- `agent_id` (str): Requesting agent identifier
- `agent_type` (str): Agent type
- `insight_types` (list, optional): Types of insights to request
- `limit` (int, optional): Maximum number of insights

**Response:**

```python
StepResult(
    success=True,
    data=[
        {
            "insight_id": "uuid-string",
            "title": "Insight Title",
            "description": "Insight description",
            "confidence_score": 0.85,
            "shared_by": "agent_1"
        }
    ]
)
```

### CrossAgentLearningService

#### `learn_from_experience`

Learn from agent experiences.

**Parameters:**

- `agent_id` (str): Agent identifier
- `experience_type` (str): Type of experience
- `context` (dict): Experience context
- `metadata` (dict, optional): Additional metadata

**Response:**

```python
StepResult(
    success=True,
    data={
        "learning_id": "uuid-string",
        "patterns_extracted": [...],
        "confidence": 0.80
    }
)
```

### CollectiveIntelligenceService

#### `synthesize_collective_intelligence`

Synthesize collective intelligence from agent contributions.

**Parameters:**

- `synthesis_type` (str): Type of synthesis
- `agent_contributions` (list): Agent contributions
- `tenant_id` (str): Tenant identifier
- `workspace_id` (str): Workspace identifier

**Response:**

```python
StepResult(
    success=True,
    data={
        "synthesis_id": "uuid-string",
        "collective_insight": "Synthesized insight",
        "contributors": [...],
        "confidence": 0.90
    }
)
```

## Observability API

### UnifiedMetricsCollector

#### `collect_system_metric`

Collect a system-level metric.

**Parameters:**

- `name` (str): Metric name
- `value` (float): Metric value
- `metric_type` (str): Type of metric (gauge, counter, histogram)
- `category` (str): Metric category
- `labels` (dict, optional): Metric labels
- `description` (str, optional): Metric description

**Response:**

```python
StepResult(
    success=True,
    data={
        "metric_id": "uuid-string",
        "collected_at": "2024-01-01T00:00:00Z"
    }
)
```

#### `collect_agent_metric`

Collect an agent-specific metric.

**Parameters:**

- `agent_id` (str): Agent identifier
- `agent_type` (str): Agent type
- `metric_name` (str): Metric name
- `value` (float): Metric value
- `metric_type` (str): Type of metric
- `category` (str): Metric category

**Response:**

```python
StepResult(
    success=True,
    data={
        "metric_id": "uuid-string",
        "collected_at": "2024-01-01T00:00:00Z"
    }
)
```

### IntelligentAlertingService

#### `create_alert_rule`

Create an alert rule.

**Parameters:**

- `rule_id` (str): Rule identifier
- `name` (str): Rule name
- `description` (str): Rule description
- `alert_type` (str): Type of alert
- `alert_level` (str): Alert level
- `conditions` (list): Alert conditions
- `enabled` (bool, optional): Whether rule is enabled

**Response:**

```python
StepResult(
    success=True,
    data={
        "rule_id": "uuid-string",
        "created_at": "2024-01-01T00:00:00Z"
    }
)
```

#### `evaluate_metric_for_alerts`

Evaluate a metric for alerts.

**Parameters:**

- `metric_name` (str): Metric name
- `value` (float): Metric value
- `timestamp` (datetime, optional): Metric timestamp
- `labels` (dict, optional): Metric labels

**Response:**

```python
StepResult(
    success=True,
    data={
        "alerts_triggered": [...],
        "evaluated_at": "2024-01-01T00:00:00Z"
    }
)
```

### DashboardIntegrationService

#### `create_grafana_dashboard`

Create a Grafana dashboard.

**Parameters:**

- `dashboard_id` (str): Dashboard identifier
- `title` (str): Dashboard title
- `description` (str): Dashboard description
- `dashboard_type` (str): Dashboard type
- `widgets` (list): Dashboard widgets
- `tags` (list, optional): Dashboard tags

**Response:**

```python
StepResult(
    success=True,
    data={
        "dashboard_id": "uuid-string",
        "created_at": "2024-01-01T00:00:00Z",
        "url": "https://grafana.example.com/dashboard/uuid-string"
    }
)
```

#### `execute_metrics_query`

Execute a metrics query.

**Parameters:**

- `query` (str): Query string
- `range_time` (str, optional): Time range
- `step` (str, optional): Query step
- `timeout` (int, optional): Query timeout

**Response:**

```python
StepResult(
    success=True,
    data={
        "results": [...],
        "executed_at": "2024-01-01T00:00:00Z"
    }
)
```

## Error Handling

### Error Response Format

All APIs return errors in the following format:

```python
StepResult(
    success=False,
    error="Error message",
    status="error_type"
)
```

### Common Error Types

- `bad_request`: Invalid input parameters
- `unauthorized`: Authentication required
- `forbidden`: Access denied
- `not_found`: Resource not found
- `rate_limited`: Rate limit exceeded
- `internal_error`: Internal server error

### Error Examples

```python
# Bad request
StepResult(
    success=False,
    error="Invalid tenant_id format",
    status="bad_request"
)

# Unauthorized
StepResult(
    success=False,
    error="Authentication required",
    status="unauthorized"
)

# Rate limited
StepResult(
    success=False,
    error="Rate limit exceeded. Try again in 60 seconds.",
    status="rate_limited"
)
```

## Authentication

### API Key Authentication

All API calls require authentication via API key:

```python
headers = {
    "Authorization": "Bearer your-api-key",
    "Content-Type": "application/json"
}
```

### Tenant Context

All operations require tenant and workspace context:

```python
tenant_id = "your-tenant-id"
workspace_id = "your-workspace-id"
```

## Rate Limiting

### Limits

- **Standard Users**: 100 requests/minute
- **Premium Users**: 1000 requests/minute
- **Enterprise Users**: 10000 requests/minute

### Rate Limit Headers

```python
# Response headers
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1640995200
```

## Webhooks

### Webhook Events

- `task.completed`: Task completion notification
- `alert.triggered`: Alert trigger notification
- `metric.threshold_exceeded`: Metric threshold exceeded

### Webhook Payload

```python
{
    "event": "task.completed",
    "data": {
        "task_id": "uuid-string",
        "status": "completed",
        "result": {...}
    },
    "timestamp": "2024-01-01T00:00:00Z"
}
```

## SDK Examples

### Python SDK

```python
from ultimate_discord_intelligence_bot import UnifiedSystemClient

client = UnifiedSystemClient(
    api_key="your-api-key",
    tenant_id="your-tenant-id",
    workspace_id="your-workspace-id"
)

# Store content
result = await client.knowledge.store_content(
    content="Sample content",
    metadata={"source": "sdk"}
)

# Route request
result = await client.router.route_request(
    prompt="Sample prompt",
    max_tokens=100
)

# Cache data
result = await client.cache.store(
    key="sample_key",
    value="sample_value",
    ttl=3600
)
```

### JavaScript SDK

```javascript
const { UnifiedSystemClient } = require('ultimate-discord-intelligence-bot');

const client = new UnifiedSystemClient({
    apiKey: 'your-api-key',
    tenantId: 'your-tenant-id',
    workspaceId: 'your-workspace-id'
});

// Store content
const result = await client.knowledge.storeContent({
    content: 'Sample content',
    metadata: { source: 'sdk' }
});

// Route request
const result = await client.router.routeRequest({
    prompt: 'Sample prompt',
    maxTokens: 100
});
```

## Best Practices

### Performance

- Use caching for frequently accessed data
- Implement proper error handling
- Monitor API usage and costs
- Use batch operations when possible

### Security

- Always use HTTPS
- Rotate API keys regularly
- Implement proper input validation
- Monitor for suspicious activity

### Reliability

- Implement retry logic with exponential backoff
- Handle rate limiting gracefully
- Use circuit breakers for external services
- Monitor system health and performance
