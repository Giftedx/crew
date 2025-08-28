# Configuration Reference

This document provides comprehensive documentation for all configuration files and their options. Configuration controls system behavior, feature flags, tenant settings, and security policies.

## Configuration Structure

```
config/                    # Global configuration
├── archive_routes.yaml    # Discord archiver routing  
├── grounding.yaml        # Citation requirements
├── ingest.yaml          # Content ingestion settings
├── policy.yaml          # Retention and governance policies
├── poller.yaml          # Scheduler and polling configuration
└── security.yaml        # Security controls and permissions

tenants/                   # Tenant-specific overrides
├── default/
│   ├── tenant.yaml       # Tenant metadata
│   ├── routing.yaml      # Model routing preferences  
│   ├── budgets.yaml      # Cost limits and budgets
│   └── policy_overrides.yaml  # Policy customizations
```

## Global Configuration Files

### Security Configuration

**File:** `config/security.yaml`

Controls authentication, authorization, rate limiting, and content moderation.

```yaml
# Role-based permissions
role_permissions:
  viewer: []                    # Read-only access
  user: []                     # Basic user permissions  
  moderator:                   # Content moderation
    - security.view
  ops:                         # Operations access
    - security.view
    - ingest.backfill
  admin:                       # Full administrative access
    - "*"

# API rate limiting
rate_limits:
  default_per_minute: 60       # Default requests per minute
  # Note: burst_allowance not currently implemented
  
# Content moderation  
moderation:
  banned_terms:                # Automatically filtered terms
    - banned
    - inappropriate
  action: redact               # Action: redact, block, flag
  confidence_threshold: 0.8    # Moderation confidence level
```

**Supported Permissions:**
- `security.view` - View security logs and metrics
- `ingest.backfill` - Trigger content backfill operations
- `*` - Wildcard for all permissions

**Rate Limit Scopes:**
- Per-user limits based on authentication
- Per-IP limits for anonymous access  
- Per-tenant global limits

**Note:** The `burst_allowance` setting shown in some documentation is not currently implemented in the actual configuration.

### Grounding Configuration

**File:** `config/grounding.yaml`

Controls citation requirements and answer verification.

```yaml
# Default citation requirements
defaults:
  min_citations: 1             # Minimum citations required
  require_timestamped: false   # Require timestamp citations
  max_response_length: 2000    # Maximum response length
  
# Command-specific overrides
commands:
  context:                     # /context command
    min_citations: 3
    require_timestamped: false
  latest:                      # /latest command  
    min_citations: 2
    require_timestamped: true
    
# Citation formats
citation_styles:
  default: "[{index}]"         # [1][2][3] format
  academic: "({source}, {timestamp})"
  
# Verification settings
verification:
  check_source_accessibility: true
  validate_timestamps: true
  confidence_threshold: 0.7
```

### Ingestion Configuration  

**File:** `config/ingest.yaml`

Controls content ingestion pipeline behavior.

```yaml
# Platform enablement
youtube:
  enabled: true                # Enable YouTube ingestion
  
twitch:
  enabled: true                # Enable Twitch ingestion
  
# Content chunking settings
chunk:
  max_chars: 800               # Characters per chunk
  overlap: 200                 # Overlap between chunks
```

**Platform Settings:**
- Each platform can be individually enabled/disabled
- Quality and extraction settings are handled by the download tools
- Platform-specific settings like `max_duration` are configured at the tool level

**Processing Settings:**
- Chunking parameters control how content is split for vector storage
- Overlap ensures context continuity between chunks

**Feature Flags Affecting Ingestion:**

While most ingestion behavior is configured via YAML, several runtime behavior
toggles are exposed as environment variables:

| Flag | Default | Description |
|------|---------|-------------|
| `ENABLE_INGEST_CONCURRENT` | unset | When set, fetches source metadata and transcript concurrently (threaded) to reduce latency. Safe fallback to sequential on error. |

These flags are intentionally environment-driven (not YAML) to allow fast
operational toggling without a config reload cycle. Keep them consistent across
workers to avoid performance variability.

### Policy Configuration

**File:** `config/policy.yaml`

Defines data privacy policies, PII detection, source control, and command limitations.

```yaml
# Allowed content sources by platform
allowed_sources:
  youtube: []                  # YouTube channel/user allowlist
  twitch: []                   # Twitch channel allowlist
  podcast: []                  # Podcast source allowlist
  official_social: []          # Official social media accounts
  web_archive: []              # Archive.org and similar

# Forbidden file types for security
forbidden_types:
  - executable
  - script
  - installer
  - unknown

# PII detection and masking (key = replacement format)
pii_types:
  email: "[redacted-email]"
  phone: "[redacted-phone]"
  ip: "[redacted-ip]"
  credit_like: "[redacted-credit]"
  gov_id_like: "[redacted-gov-id]"
  address_like: "[redacted-address]"
  geo_exact: "[redacted-geo]"

# PII masking configurations (mirrors pii_types)
masks:
  email: "[redacted-email]"
  phone: "[redacted-phone]" 
  ip: "[redacted-ip]"
  credit_like: "[redacted-credit]"
  gov_id_like: "[redacted-gov-id]"
  address_like: "[redacted-address]"
  geo_exact: "[redacted-geo]"

# Data storage policies
storage:
  max_retention_days_by_ns:
    default: 30                # Default retention in days
  cache_ttl_overrides: {}      # Namespace-specific cache TTL

# User consent management
consent:
  allow_quotes: true           # Allow content quotation
  allow_thumbnails: true       # Allow thumbnail generation
  allow_embed: true            # Allow content embedding
  allow_snippets: true         # Allow snippet extraction

# Per-command limitations and settings
per_command:
  /context:
    max_tokens: 2048           # Maximum response tokens
    require_sources: true      # Require source citations
    speculation_forbidden: true # Prevent speculative responses
```

**PII Detection:**
- Automatically detects and masks personally identifiable information
- Uses semantic detection (e.g., `credit_like`, `gov_id_like`) rather than exact pattern matching
- Configurable replacement text for each PII type

**Source Control:**
- Platform-specific allowlists for content ingestion
- Empty arrays mean all sources from that platform are allowed
- Forbidden file types prevent security risks from executable content

**Consent Management:**
- Controls what types of content processing are permitted
- Granular permissions for quotes, thumbnails, embedding, and snippets
- Can be overridden per tenant

**Command Configuration:**
- Per-command token limits and behavioral controls
- Source citation requirements
- Speculation prevention for factual accuracy

### Archive Routes Configuration

**File:** `config/archive_routes.yaml`

Controls Discord CDN archiver behavior and routing.

```yaml
# Default settings for all routes
defaults:
  max_retries: 3               # Retry failed uploads
  chunking: true               # Enable file chunking

# Content routing by type and visibility
routes:
  images:
    public:
      channel_id: "000000000000000000"
    private:
      channel_id: "000000000000000000"
  videos:
    public:
      channel_id: "000000000000000000"
    private:
      channel_id: "000000000000000000"
  audio:
    public:
      channel_id: "000000000000000000"  
    private:
      channel_id: "000000000000000000"
  docs:
    public:
      channel_id: "000000000000000000"
    private:
      channel_id: "000000000000000000"
  blobs:                      # Binary/other file types
    public:
      channel_id: "000000000000000000"
    private:
      channel_id: "000000000000000000"

# Per-tenant routing overrides
per_tenant_overrides: {}      # Tenant-specific channel mappings
```

**Routing Logic:**
- Content is routed by both type (images, videos, audio, docs, blobs) and visibility (public/private)
- Each route specifies a Discord channel ID for archiving
- Default settings apply retry behavior and chunking options

**Channel Configuration:**
- Channel IDs must be valid Discord channels accessible by the bot
- Public/private distinction allows content access control
- Tenant overrides enable per-tenant custom routing

### Poller Configuration

**File:** `config/poller.yaml`

Controls the scheduler and content polling behavior.

```yaml
# Polling intervals by source type
intervals:
  youtube:
    channel: 3600             # Check channels hourly
    playlist: 7200            # Check playlists every 2h
    video: 86400              # Check videos daily
    
  twitch:
    stream: 300               # Check streams every 5min
    clip: 1800               # Check clips every 30min
    
  social:
    twitter: 900             # Check Twitter every 15min
    reddit: 1800             # Check Reddit every 30min
    
# Priority settings
priority:
  high_priority_sources:      # Sources checked more frequently
    - "official_channels"
    - "verified_creators"
  
  backoff_on_error:          # Exponential backoff
    initial_delay: 300       # 5 minutes
    max_delay: 86400         # 24 hours max
    multiplier: 2.0
    
# Resource limits
limits:
  max_concurrent_jobs: 5     # Parallel ingestion jobs
  max_queue_size: 1000      # Maximum queued items
  timeout_seconds: 300      # Job timeout
```

## Tenant Configuration

Each tenant has its own configuration directory under `tenants/<slug>/`.
For example, the default tenant has files in `tenants/default/`.

### Tenant Metadata

**File:** `tenants/<slug>/tenant.yaml`

```yaml
# Tenant identification
name: "Default Tenant"
slug: "default"
description: "Default tenant for development"

# Contact information
contact:
  email: "admin@example.com"
  discord: "@admin#1234"
  
# Tenant settings
settings:
  timezone: "UTC"
  language: "en"
  region: "us-east-1"
  
# Feature enablement
features:
  rl_enabled: true            # Reinforcement learning
  grounding_enabled: true     # Citation requirements
  archiver_enabled: true     # Discord archiver
  
# Workspace configuration
workspaces:
  main:                       # Primary workspace
    description: "Main workspace"
    default: true
  test:                       # Test workspace
    description: "Testing and development"
```

### Model Routing Configuration

**File:** `tenants/<slug>/routing.yaml`

```yaml
# Provider preferences (in order of preference)
providers:
  - openrouter              # Primary provider
  - openai                  # Fallback provider
  
# Model preferences by use case
models:
  default: "anthropic/claude-3-sonnet"
  
  # Specialized models
  debate: "openai/gpt-4"
  summarization: "anthropic/claude-3-haiku" 
  code: "anthropic/claude-3-sonnet"
  creative: "openai/gpt-4"
  
# Routing policies
routing:
  strategy: "cost_optimized"   # cost_optimized, performance, balanced
  fallback_enabled: true       # Use fallback on failure
  retry_attempts: 3            # Retry failed requests
  
# Context windows
context_limits:
  default: 32000               # Default context window
  long_context: 128000         # Long context for complex tasks
```

### Budget Configuration

**File:** `tenants/<slug>/budgets.yaml`

```yaml
# Monthly budgets in USD
budgets:
  monthly_total: 1000.00      # Total monthly budget
  
  # Per-category budgets
  by_category:
    ingestion: 300.00         # Content ingestion
    qa: 400.00               # Q&A responses  
    debate: 200.00           # Debate sessions
    analysis: 100.00         # Content analysis
    
# Per-request limits
limits:
  max_per_request: 5.00      # Maximum cost per request
  daily_limit: 50.00         # Daily spending limit
  burst_allowance: 20.00     # Burst spending allowance
  
# Cost tracking
tracking:
  alert_thresholds:           # Alert at spending percentages
    - 50    # 50% of budget
    - 80    # 80% of budget  
    - 95    # 95% of budget
  
  cost_categories:           # Track costs by category
    - model_inference
    - vector_storage
    - external_apis
```

### Policy Overrides

**File:** `tenants/<slug>/policy_overrides.yaml`

```yaml
# Override global PII detection settings
pii_overrides:
  additional_types:            # Additional PII types for this tenant
    - custom_identifier
  masks:                       # Custom mask formats
    email: "[TENANT_EMAIL]"
    
# Source control overrides
source_overrides:
  additional_allowed:          # Additional allowed sources
    - internal-wiki.company.com
  additional_forbidden:        # Additional forbidden types
    - zip
    - tar
    
# Command limit overrides  
command_overrides:
  context:
    max_requests_per_hour: 20  # Higher limit for this tenant
    
# Consent overrides
consent_overrides:
  prompt_frequency: 90         # Less frequent consent prompts
  custom_message: "Custom consent text for this tenant"
  
# Storage overrides
storage_overrides:
  retention_days: 180          # Shorter retention
  encrypt_pii: true           # Ensure PII encryption
```

## Feature Flags

Feature flags are controlled via environment variables and can be overridden in tenant configuration.

### Core Feature Flags

```bash
# Ingestion features
ENABLE_INGEST_YOUTUBE=true     # YouTube content ingestion
ENABLE_INGEST_TWITCH=true      # Twitch content ingestion  
ENABLE_INGEST_TIKTOK=true      # TikTok content ingestion

# RAG and context features
ENABLE_RAG_CONTEXT=true        # RAG-based context retrieval
ENABLE_VECTOR_SEARCH=true      # Vector similarity search
ENABLE_GROUNDING=true          # Citation enforcement

# Caching and performance
ENABLE_CACHE=true              # Response caching
ENABLE_CACHE_LLM=true         # LLM response caching
ENABLE_CACHE_VECTOR=true      # Vector search caching

# Reinforcement learning
ENABLE_RL_GLOBAL=true         # Global RL system
ENABLE_RL_ROUTING=true        # RL-based model routing
ENABLE_RL_PROMPT=true         # RL-based prompt optimization
ENABLE_RL_RETRIEVAL=true      # RL-based retrieval optimization

# Discord integrations
ENABLE_DISCORD_ARCHIVER=true  # Discord CDN archiver
ENABLE_DISCORD_COMMANDS=true  # Discord slash commands
ENABLE_DISCORD_MONITOR=true   # Discord activity monitoring

# Security and privacy
ENABLE_PII_DETECTION=true     # PII detection and redaction
ENABLE_CONTENT_MODERATION=true # Content moderation
ENABLE_RATE_LIMITING=true     # API rate limiting

# Observability
ENABLE_TRACING=true           # OpenTelemetry tracing
ENABLE_METRICS=true           # Prometheus metrics
ENABLE_AUDIT_LOGGING=true     # Audit log collection
```

### Flag Hierarchies

Feature flags follow a hierarchy:
1. **Environment variables** (highest priority)
2. **Tenant feature overrides** (medium priority)  
3. **Global defaults** (lowest priority)

### Dynamic Feature Flags

Some features can be toggled at runtime:

```python
from core.flags import enabled

if enabled("ENABLE_EXPERIMENTAL_FEATURE"):
    # Experimental code path
    pass
```

## Configuration Validation

Configuration files are validated on startup:

```python
# Validation errors logged and prevent startup
ERROR: Invalid grounding.yaml: min_citations must be >= 1
ERROR: Missing required tenant.yaml field: name
```

## Environment Variable Reference

### Required Variables

```bash
# API Keys (at least one required)
OPENAI_API_KEY=sk-...         # OpenAI API key
OPENROUTER_API_KEY=sk-...     # OpenRouter API key

# Discord Integration
DISCORD_WEBHOOK_URL=https://... # Discord webhook for notifications
DISCORD_PRIVATE_WEBHOOK_URL=https://... # Private alerts webhook

# Vector Database
QDRANT_URL=http://localhost:6333 # Qdrant instance URL
QDRANT_API_KEY=...               # Qdrant API key (if required)
```

### Optional Variables

```bash
# Database Configuration  
DATABASE_URL=sqlite:///crew.db   # Database connection string
MEMORY_DB_PATH=./memory.db       # Memory database path

# External Services
GOOGLE_API_KEY=...               # Google services API key
PERSPECTIVE_API_KEY=...          # Content moderation API

# Performance Tuning
MAX_WORKERS=4                    # Thread pool size
CACHE_TTL_SECONDS=3600          # Cache time-to-live
VECTOR_BATCH_SIZE=100           # Vector operation batch size

# Development/Debug
DEBUG=false                      # Debug mode
LOG_LEVEL=INFO                  # Logging level
ENABLE_PROFILING=false          # Performance profiling
```

## Configuration Best Practices

### Security
- Store sensitive keys in environment variables, not config files
- Use different configurations for development/staging/production
- Rotate API keys regularly  
- Enable audit logging in production

### Performance
- Tune chunk sizes based on your embedding model
- Adjust rate limits based on usage patterns
- Configure appropriate cache TTLs
- Monitor resource usage and adjust limits

### Tenant Management
- Use descriptive tenant slugs
- Set appropriate budget limits
- Configure retention policies based on data sensitivity
- Test policy overrides in non-production environments

### Monitoring
- Enable all observability features in production
- Set up alerting for budget thresholds
- Monitor configuration changes via audit logs
- Test configuration changes in staging first

## See Also

- [Tenancy Documentation](tenancy.md) - Multi-tenant architecture
- [Security Documentation](security/) - Security model details  
- [Observability Documentation](observability.md) - Monitoring and metrics
- [Cost and Caching Documentation](cost_and_caching.md) - Budget management