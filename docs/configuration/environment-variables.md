# Environment Variables Configuration

## Overview

The Ultimate Discord Intelligence Bot uses environment variables for configuration management. This document provides a comprehensive reference for all available configuration options.

## Core Configuration

### Application Settings

```bash
# Application name and version
APP_NAME=Ultimate Discord Intelligence Bot
APP_VERSION=1.0.0
APP_ENV=production  # development, staging, production

# Logging configuration
LOG_LEVEL=INFO  # DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_FORMAT=json  # json, text
LOG_FILE=/var/log/discord-bot.log
```

### Database Configuration

```bash
# Qdrant Vector Database
QDRANT_URL=http://localhost:6333
QDRANT_API_KEY=your_qdrant_api_key
QDRANT_TIMEOUT=30
QDRANT_RETRY_ATTEMPTS=3

# Collection Configuration
QDRANT_COLLECTION_CACHE_HITS=cache_hits
QDRANT_COLLECTION_ARTIFACTS=artifacts
QDRANT_COLLECTION_EMBEDDINGS=embeddings
```

## Vector Memory Configuration

### Embedding Service

```bash
# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=text-embedding-3-small
OPENAI_EMBEDDING_DIMENSION=1536

# Local Embedding Models
ENABLE_LOCAL_EMBEDDINGS=true
LOCAL_EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
LOCAL_EMBEDDING_DEVICE=cpu  # cpu, cuda, mps

# Embedding Configuration
EMBEDDING_BATCH_SIZE=100
EMBEDDING_MAX_LENGTH=512
EMBEDDING_CACHE_SIZE=1000
```

### Memory Service

```bash
# Memory Service Settings
ENABLE_VECTOR_MEMORY=true
MEMORY_CACHE_TTL=3600  # seconds
MEMORY_MAX_CACHE_SIZE=10000
MEMORY_CLEANUP_INTERVAL=300  # seconds

# Search Configuration
SEARCH_LIMIT=10
SEARCH_SCORE_THRESHOLD=0.7
SEARCH_TIMEOUT=5  # seconds
```

## RL Routing Configuration

### Bandit Policy

```bash
# RL Routing Settings
ENABLE_RL_ROUTING=true
BANDIT_ALPHA_PRIOR=1.0
BANDIT_BETA_PRIOR=1.0
BANDIT_EXPLORATION_RATE=0.2
BANDIT_LEARNING_RATE=0.1

# Provider Configuration
AVAILABLE_PROVIDERS=openai,anthropic,cohere
DEFAULT_PROVIDER=openai
PROVIDER_TIMEOUT=30  # seconds
PROVIDER_RETRY_ATTEMPTS=3
```

### Routing Service

```bash
# Routing Configuration
ROUTING_STRATEGY=bandit  # bandit, round_robin, random
ROUTING_WEIGHT_ACCURACY=0.4
ROUTING_WEIGHT_LATENCY=0.3
ROUTING_WEIGHT_COST=0.3
ROUTING_FEEDBACK_WINDOW=100  # requests
```

## MCP Tools Configuration

### MCP Client

```bash
# MCP Server Configuration
ENABLE_MCP_TOOLS=true
MCP_BASE_URL=https://api.mcp.io
MCP_API_KEY=your_mcp_api_key
MCP_TIMEOUT=30  # seconds
MCP_RETRY_ATTEMPTS=3

# Tool Configuration
MCP_TOOL_TIMEOUT=60  # seconds
MCP_TOOL_RATE_LIMIT=100  # requests per minute
MCP_TOOL_CACHE_TTL=300  # seconds
```

### Available MCP Tools

```bash
# Web Search Tool
ENABLE_WEB_SEARCH=true
WEB_SEARCH_API_KEY=your_search_api_key
WEB_SEARCH_RESULTS_LIMIT=10
WEB_SEARCH_TIMEOUT=10  # seconds

# Image Analysis Tool
ENABLE_IMAGE_ANALYSIS=true
IMAGE_ANALYSIS_API_KEY=your_vision_api_key
IMAGE_ANALYSIS_MAX_SIZE=10  # MB
IMAGE_ANALYSIS_TIMEOUT=30  # seconds

# Data Analysis Tool
ENABLE_DATA_ANALYSIS=true
DATA_ANALYSIS_MAX_ROWS=10000
DATA_ANALYSIS_TIMEOUT=60  # seconds

# Code Review Tool
ENABLE_CODE_REVIEW=true
CODE_REVIEW_MAX_LINES=1000
CODE_REVIEW_TIMEOUT=30  # seconds
```

## Prompt Optimization Configuration

### Prompt Compressor

```bash
# Prompt Optimization Settings
ENABLE_PROMPT_OPTIMIZATION=true
TARGET_COMPRESSION_RATIO=0.5
MIN_QUALITY_THRESHOLD=0.8
PRESERVE_STRUCTURE=true
AGGRESSIVE_MODE=false

# Compression Configuration
COMPRESSION_STRATEGIES=whitespace,patterns,sentences,words
COMPRESSION_BATCH_SIZE=10
COMPRESSION_TIMEOUT=5  # seconds
```

### Optimization Pipeline

```bash
# Optimization Settings
OPTIMIZATION_ENABLE_CACHING=true
OPTIMIZATION_ENABLE_QUALITY_VALIDATION=true
OPTIMIZATION_TARGET_COST_REDUCTION=0.3
OPTIMIZATION_MAX_TIME_MS=5000
OPTIMIZATION_QUALITY_THRESHOLD=0.8
```

## Discord Publishing Configuration

### Discord Integration

```bash
# Discord Bot Configuration
DISCORD_BOT_TOKEN=your_discord_bot_token
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/...
DISCORD_CHANNEL_ID=your_channel_id
DISCORD_GUILD_ID=your_guild_id

# Publishing Settings
ENABLE_DISCORD_PUBLISHING=true
DISCORD_ENABLE_EMBEDS=true
DISCORD_MAX_MESSAGE_LENGTH=2000
DISCORD_ENABLE_FILE_UPLOADS=true
DISCORD_MAX_FILE_SIZE_MB=8
```

### Artifact Publishing

```bash
# Artifact Configuration
ARTIFACT_PUBLISHING_ENABLED=true
ARTIFACT_BATCH_SIZE=10
ARTIFACT_PUBLISHING_TIMEOUT=30  # seconds
ARTIFACT_RETRY_ATTEMPTS=3

# Content Types
ENABLE_ANALYSIS_ARTIFACTS=true
ENABLE_TRANSCRIPT_ARTIFACTS=true
ENABLE_VERIFICATION_ARTIFACTS=true
ENABLE_SUMMARY_ARTIFACTS=true
```

## Observability Configuration

### Metrics Collection

```bash
# Observability Settings
ENABLE_OBSERVABILITY=true
METRICS_ENDPOINT=http://localhost:9090
METRICS_BATCH_SIZE=100
METRICS_FLUSH_INTERVAL=30  # seconds

# Metrics Configuration
ENABLE_HISTOGRAMS=true
ENABLE_COUNTERS=true
ENABLE_GAUGES=true
METRICS_RETENTION_DAYS=30
```

### Logging Configuration

```bash
# Logging Settings
LOG_LEVEL=INFO
LOG_FORMAT=json
LOG_FILE=/var/log/discord-bot.log
LOG_MAX_SIZE=100  # MB
LOG_BACKUP_COUNT=5
LOG_ROTATION_INTERVAL=daily

# Structured Logging
LOG_INCLUDE_TIMESTAMP=true
LOG_INCLUDE_LEVEL=true
LOG_INCLUDE_LOGGER=true
LOG_INCLUDE_MESSAGE=true
```

### Health Monitoring

```bash
# Health Check Settings
HEALTH_CHECK_ENABLED=true
HEALTH_CHECK_INTERVAL=30  # seconds
HEALTH_CHECK_TIMEOUT=5  # seconds
HEALTH_CHECK_RETRY_ATTEMPTS=3

# Component Health
VECTOR_MEMORY_HEALTH_CHECK=true
RL_ROUTING_HEALTH_CHECK=true
MCP_TOOLS_HEALTH_CHECK=true
PROMPT_OPTIMIZATION_HEALTH_CHECK=true
DISCORD_PUBLISHING_HEALTH_CHECK=true
```

## Security Configuration

### Authentication

```bash
# API Authentication
API_KEY_REQUIRED=true
API_KEY_HEADER=X-API-Key
API_KEY_VALIDATION=true

# JWT Configuration
JWT_SECRET_KEY=your_jwt_secret_key
JWT_ALGORITHM=HS256
JWT_EXPIRATION_TIME=3600  # seconds
```

### Data Protection

```bash
# Encryption Settings
ENCRYPTION_ENABLED=true
ENCRYPTION_KEY=your_encryption_key
ENCRYPTION_ALGORITHM=AES-256-GCM

# Data Retention
DATA_RETENTION_DAYS=90
AUTO_CLEANUP_ENABLED=true
CLEANUP_INTERVAL=24  # hours
```

### Privacy Settings

```bash
# Privacy Configuration
PRIVACY_FILTER_ENABLED=true
PII_DETECTION_ENABLED=true
PII_MASKING_ENABLED=true
DATA_ANONYMIZATION_ENABLED=true

# GDPR Compliance
GDPR_COMPLIANCE_MODE=true
USER_CONSENT_REQUIRED=true
DATA_PORTABILITY_ENABLED=true
RIGHT_TO_BE_FORGOTTEN=true
```

## Performance Configuration

### Resource Limits

```bash
# Memory Configuration
MAX_MEMORY_USAGE=2  # GB
MEMORY_CLEANUP_THRESHOLD=0.8
MEMORY_MONITORING_ENABLED=true

# CPU Configuration
MAX_CPU_USAGE=0.8
CPU_MONITORING_ENABLED=true
PARALLEL_PROCESSING_LIMIT=4
```

### Caching Configuration

```bash
# Cache Settings
CACHE_ENABLED=true
CACHE_TTL=3600  # seconds
CACHE_MAX_SIZE=10000
CACHE_CLEANUP_INTERVAL=300  # seconds

# Redis Configuration (if used)
REDIS_URL=redis://localhost:6379
REDIS_PASSWORD=your_redis_password
REDIS_DB=0
REDIS_TIMEOUT=5  # seconds
```

## Development Configuration

### Debug Settings

```bash
# Debug Configuration
DEBUG_MODE=false
DEBUG_LOGGING=false
DEBUG_METRICS=false
DEBUG_TRACING=false

# Development Tools
ENABLE_PROFILING=false
ENABLE_MEMORY_PROFILING=false
ENABLE_CPU_PROFILING=false
```

### Testing Configuration

```bash
# Test Settings
TEST_MODE=false
TEST_DATABASE_URL=sqlite:///test.db
TEST_CACHE_ENABLED=false
TEST_MOCK_EXTERNAL_APIS=true

# Test Data
TEST_DATA_PATH=./test_data/
TEST_FIXTURES_PATH=./test_fixtures/
```

## Deployment Configuration

### Docker Configuration

```bash
# Docker Settings
DOCKER_IMAGE_TAG=latest
DOCKER_REGISTRY=your-registry.com
DOCKER_NAMESPACE=discord-bot

# Container Configuration
CONTAINER_MEMORY_LIMIT=2g
CONTAINER_CPU_LIMIT=1
CONTAINER_RESTART_POLICY=unless-stopped
```

### Kubernetes Configuration

```bash
# Kubernetes Settings
K8S_NAMESPACE=discord-bot
K8S_REPLICAS=3
K8S_RESOURCE_LIMITS_CPU=1
K8S_RESOURCE_LIMITS_MEMORY=2Gi
K8S_RESOURCE_REQUESTS_CPU=0.5
K8S_RESOURCE_REQUESTS_MEMORY=1Gi
```

## Configuration Validation

### Required Variables

The following environment variables are required for basic operation:

```bash
# Core Requirements
QDRANT_URL
OPENAI_API_KEY
DISCORD_BOT_TOKEN

# Optional but Recommended
ENABLE_RL_ROUTING=true
ENABLE_MCP_TOOLS=true
ENABLE_PROMPT_OPTIMIZATION=true
ENABLE_DISCORD_PUBLISHING=true
ENABLE_OBSERVABILITY=true
```

### Configuration Validation

The system validates configuration on startup:

1. **Required Variables**: Checks for all required environment variables
2. **Format Validation**: Validates URL formats, API keys, and other structured data
3. **Connectivity Tests**: Tests connections to external services
4. **Resource Availability**: Checks for sufficient system resources

### Configuration Examples

#### Development Environment

```bash
# .env.development
APP_ENV=development
LOG_LEVEL=DEBUG
DEBUG_MODE=true
QDRANT_URL=http://localhost:6333
OPENAI_API_KEY=your_dev_key
DISCORD_BOT_TOKEN=your_dev_token
```

#### Production Environment

```bash
# .env.production
APP_ENV=production
LOG_LEVEL=INFO
DEBUG_MODE=false
QDRANT_URL=https://qdrant.production.com
OPENAI_API_KEY=your_prod_key
DISCORD_BOT_TOKEN=your_prod_token
ENABLE_OBSERVABILITY=true
METRICS_ENDPOINT=https://metrics.production.com
```

## Troubleshooting

### Common Configuration Issues

1. **Missing Environment Variables**: Check that all required variables are set
2. **Invalid URLs**: Ensure URLs are properly formatted and accessible
3. **Authentication Failures**: Verify API keys and tokens are valid
4. **Resource Limits**: Check that system resources are sufficient

### Configuration Testing

```bash
# Test configuration
python -m ultimate_discord_intelligence_bot.config.validate

# Test specific components
python -m ultimate_discord_intelligence_bot.services.test_connectivity
```

### Configuration Documentation

For more detailed configuration options, see:

- [Architecture Documentation](../architecture/multi-agent-orchestration.md)
- [API Documentation](../api/)
- [Deployment Guide](../deployment/)
