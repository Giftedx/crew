# API Reference Guide

This document provides comprehensive API documentation for the Ultimate Discord Intelligence Bot system, including service interfaces, tool APIs, and integration endpoints.

## Core Services API

### Memory Service

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
