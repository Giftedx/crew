# Tools Reference Guide

This document provides comprehensive documentation for all available CrewAI tools in the system. Tools are organized by category and functionality.

> Network & HTTP Conventions: See `docs/network_conventions.md` for canonical outbound HTTP guidance (timeouts, URL validation, resilient POST/GET helpers, rate‑limit handling, optional retry/backoff & tracing). Tools performing network I/O should rely on `src/core/http_utils.py` (`resilient_post`, `resilient_get`, `retrying_post`, `retrying_get`, `http_request_with_retry`, constants) rather than re‑implementing validation, timeouts, or monkeypatch‑friendly fallbacks.

## Content Analysis Tools

### Logical Fallacy Tool
**File:** `src/ultimate_discord_intelligence_bot/tools/logical_fallacy_tool.py`

Detects logical fallacies in text using sophisticated pattern matching and heuristics. Enhanced beyond basic keyword matching to include complex linguistic patterns. A prior backup variant was removed as dead code to avoid duplication; this canonical implementation defines explicit heuristic threshold constants for maintainability.

**Features:**
- 17+ fallacy types including ad hominem, straw man, false dilemma, slippery slope
- Keyword-based detection (`KEYWORD_FALLACIES`)  
- Regex pattern matching (`PATTERN_FALLACIES`)
- Confidence scoring and detailed explanations
- Context-aware analysis

**Usage:**
```python
from ultimate_discord_intelligence_bot.tools.logical_fallacy_tool import LogicalFallacyTool

tool = LogicalFallacyTool()
result = tool._run("Everyone knows this is true, so you must agree.")
# Returns: detected fallacies with confidence scores
```

### Claim Extractor Tool
**File:** `src/ultimate_discord_intelligence_bot/tools/claim_extractor_tool.py`

Extracts factual claims from text using knowledge graph extraction patterns.

**Features:**
- Integration with KG extraction utilities (`kg.extract`)
- Filters out short/insignificant matches
- Returns structured claim data
- NLP-based pattern recognition

**Usage:**
```python
result = tool._run("The Earth is round and orbits the Sun.")
# Returns: {"status": "success", "claims": ["The Earth is round", "Earth orbits the Sun"]}
```

### Perspective Synthesizer Tool  
**File:** `src/ultimate_discord_intelligence_bot/tools/perspective_synthesizer_tool.py`

Combines multiple search results into a coherent, unified summary using LLM processing.

**Features:**
- Merges search backends (memory, vector, external)
- Memory retrieval integration
- OpenRouter service integration
- Prompt engine processing

**Dependencies:**
- `MemoryService` - Retrieves relevant memories
- `OpenRouterService` - LLM processing  
- `PromptEngine` - Prompt construction

### Steelman Argument Tool
**File:** `src/ultimate_discord_intelligence_bot/tools/steelman_argument_tool.py`

Creates the strongest possible version of arguments for debate analysis.

### Sentiment Tool
**File:** `src/ultimate_discord_intelligence_bot/tools/sentiment_tool.py`

Analyzes emotional tone and sentiment in text content. Uses VADER when available; otherwise falls back to a lightweight lexical heuristic. Thresholds (`POSITIVE_THRESHOLD`, `NEGATIVE_THRESHOLD`) are declared as module constants for clarity.

### Text Analysis Tool
**File:** `src/ultimate_discord_intelligence_bot/tools/text_analysis_tool.py`

Provides general-purpose text processing and analysis capabilities.

## Data Management Tools

### Memory Storage Tool
**File:** `src/ultimate_discord_intelligence_bot/tools/memory_storage_tool.py`

Handles storage and retrieval of memory items in the unified memory layer.

**Features:**
- SQLite/Qdrant integration
- Tenant-aware storage
- Retention policy enforcement
- Pinning and archival support

### Timeline Tool
**File:** `src/ultimate_discord_intelligence_bot/tools/timeline_tool.py`

Manages chronological event tracking and timeline construction.

### Trustworthiness Tracker Tool
**File:** `src/ultimate_discord_intelligence_bot/tools/trustworthiness_tracker_tool.py`

Tracks source credibility and trustworthiness metrics over time.

**Features:**
- Source credibility scoring
- Historical tracking
- Statistical analysis
- Integration with fact-checking pipeline

## Media Processing Tools

### Audio Transcription Tool
**File:** `src/ultimate_discord_intelligence_bot/tools/audio_transcription_tool.py`

Handles audio-to-text conversion with Whisper integration.

### Multi-Platform Download Tool
**File:** `src/ultimate_discord_intelligence_bot/tools/multi_platform_download_tool.py`

Dispatcher for downloading content from multiple platforms (YouTube, Twitch, TikTok). Includes early-return design for readability, with explicit logging and normalized error responses.

**Features:**
- Platform detection via URL patterns
- Quality parameter support
- yt-dlp integration
- Consistent error handling via `StepResult`

### Discord Download Tool
**File:** `src/ultimate_discord_intelligence_bot/tools/discord_download_tool.py`

Downloads Discord-hosted attachments and files directly via HTTP requests.

**Features:**
- Direct download of Discord CDN attachments
- Stream-based downloading for large files
- Temporary file handling
- Error handling with structured responses

**Usage:**
```python
from ultimate_discord_intelligence_bot.tools.discord_download_tool import DiscordDownloadTool

tool = DiscordDownloadTool()
result = tool._run("https://cdn.discordapp.com/attachments/...")
# Returns: {"status": "success", "local_path": "/tmp/file.ext", "platform": "Discord"}
```

### yt-dlp Download Tool
**File:** `src/ultimate_discord_intelligence_bot/tools/yt_dlp_download_tool.py`

Generic yt-dlp wrapper providing reusable download functionality for video platforms. Adds an explicit `check=False` on the subprocess invocation (with justification comment) to preserve monkeypatched test compatibility while documenting security considerations.

**Features:**
- Base class for platform-specific downloaders
- Configurable quality selection with format selectors
- Archive file integration to prevent re-downloads
- Comprehensive error handling and logging
- Subprocess management for yt-dlp execution

**Usage:**
```python
# Used as base class for platform-specific tools
class CustomPlatformTool(YtDlpDownloadTool):
    platform = "custom_platform"

tool = CustomPlatformTool()
result = tool._run("https://example.com/video", quality="720p")
```

**Quality Options:**
- Format: `720p`, `1080p`, `480p`, etc.
- Automatically selects best available stream not exceeding specified resolution
- Falls back gracefully for unavailable qualities

### Platform Resolver Tools
**Directory:** `src/ultimate_discord_intelligence_bot/tools/platform_resolver/`

Specialized resolvers for platform-specific content handling and URL resolution.

**Available Resolvers:**
- **YouTube Resolver** (`youtube_resolver.py`) - Handles YouTube URL patterns and metadata extraction
- **Twitch Resolver** (`twitch_resolver.py`) - Processes Twitch streams, clips, and VODs
- **Podcast Resolver** (`podcast_resolver.py`) - Resolves podcast feeds and episode metadata
- **Social Resolver** (`social_resolver.py`) - Handles social media platform URL resolution

**Features:**
- Platform-specific URL pattern matching
- Metadata extraction and normalization
- Content type identification
- Consistent resolver interface across platforms

### YouTube Download Tool
**File:** `src/ultimate_discord_intelligence_bot/tools/youtube_download_tool.py`

YouTube-specific content downloader with metadata extraction.

## Discord Integration Tools

### Discord Post Tool  
**File:** `src/ultimate_discord_intelligence_bot/tools/discord_post_tool.py`

Posts messages, embeds, and files to Discord channels via webhooks. Delegates URL validation, timeout application, and safe request execution (including monkeypatch‑friendly fallbacks) to `core.http_utils.resilient_post` and `validate_public_https_url`. Local constants cover Discord‑specific limits (e.g. `DISCORD_FILE_LIMIT_MB`) while generic HTTP status constants come from the shared module.

### Discord QA Tool
**File:** `src/ultimate_discord_intelligence_bot/tools/discord_qa_tool.py`

Handles question-answering interactions in Discord.

### Discord Monitor Tool
**File:** `src/ultimate_discord_intelligence_bot/tools/discord_monitor_tool.py`

Monitors Discord activity and events.

### Discord Private Alert Tool
**File:** `src/ultimate_discord_intelligence_bot/tools/discord_private_alert_tool.py`

Sends private alerts and notifications. Centralized HTTP concerns (public HTTPS validation, timeout, rate‑limit aware retry for 429, and TypeError fallback when tests monkeypatch `requests.post`) are handled via `core.http_utils` helpers, keeping tool logic focused on payload construction.

## Search & Retrieval Tools

### Vector Search Tool
**File:** `src/ultimate_discord_intelligence_bot/tools/vector_search_tool.py`

Performs semantic search using vector embeddings in Qdrant.

### Context Verification Tool
**File:** `src/ultimate_discord_intelligence_bot/tools/context_verification_tool.py`

Verifies context accuracy and citation integrity.

### Fact Check Tool
**File:** `src/ultimate_discord_intelligence_bot/tools/fact_check_tool.py`

Performs fact-checking against reliable sources. Aggregates multiple backend searches (DuckDuckGo, optional API-based engines) with retry logic and tunable evidence thresholds (`EVIDENCE_WELL_SUPPORTED_THRESHOLD`, etc.). All outbound requests specify timeouts.

### Truth Scoring Tool
**File:** `src/ultimate_discord_intelligence_bot/tools/truth_scoring_tool.py`

Assigns truth/reliability scores to claims and statements.

## Social Media Tools

### Social Media Monitor Tool
**File:** `src/ultimate_discord_intelligence_bot/tools/social_media_monitor_tool.py`

Monitors social media platforms for relevant content.

### Multi-Platform Monitor Tool
**File:** `src/ultimate_discord_intelligence_bot/tools/multi_platform_monitor_tool.py`

Unified monitoring across multiple social platforms.

### X Monitor Tool
**File:** `src/ultimate_discord_intelligence_bot/tools/x_monitor_tool.py`

X (Twitter) specific monitoring and content extraction.

## System Tools

### System Status Tool
**File:** `src/ultimate_discord_intelligence_bot/tools/system_status_tool.py`

Reports system health, metrics, and performance statistics. Provides graceful degradation when `/proc` not available and logs (rather than silences) read failures.

**Features:**
- CPU load average monitoring
- Memory usage reporting
- Service health checks
- Prometheus metrics integration

### Drive Upload Tool
**File:** `src/ultimate_discord_intelligence_bot/tools/drive_upload_tool.py`

Handles file uploads to cloud storage services.

### Leaderboard Tool
**File:** `src/ultimate_discord_intelligence_bot/tools/leaderboard_tool.py`

Manages ranking and scoring systems.

## Profile & Character Tools

### Character Profile Tool
**File:** `src/ultimate_discord_intelligence_bot/tools/character_profile_tool.py`

Manages character profiles and personality data.

### Pipeline Tool
**File:** `src/ultimate_discord_intelligence_bot/tools/pipeline_tool.py`

Orchestrates multi-step processing pipelines.

### Transcript Index Tool
**File:** `src/ultimate_discord_intelligence_bot/tools/transcript_index_tool.py`

Indexes and searches transcript content.

## Command Tools

### Debate Command Tool
**File:** `src/ultimate_discord_intelligence_bot/tools/debate_command_tool.py`

Handles debate-related Discord commands and interactions.

## Configuration

Tools are configured through:
- Individual tool initialization parameters
- Global configuration files in `config/`
- Tenant-specific overrides in `tenants/<slug>/`
- Environment variables for external service integration

## Testing

Most tools have comprehensive test coverage in `tests/test_*_tool.py` files. Run the full test suite with:

```bash
pytest tests/test_*tool*.py
```

## Integration Patterns

Tools follow consistent patterns for:
- Tenant context awareness via `TenantContext`
- Error handling with structured results
- Observability through OpenTelemetry tracing
- Privacy compliance via automated filtering
- Cost management through token metering
- Centralized HTTP utilities (`core/http_utils.py`) for outbound requests (see `network_conventions.md`)
- Convenience retry wrappers: `retrying_post` / `retrying_get` (feature-flag controlled by `ENABLE_ANALYSIS_HTTP_RETRY`). These call `http_request_with_retry` when enabled; otherwise they devolve to single-attempt resilient helpers.
- Retry metrics (Prometheus counters):
    - `HTTP_RETRY_ATTEMPTS{method}` – increments for each retry attempt beyond the first.
    - `HTTP_RETRY_GIVEUPS{method}` – increments when all retry attempts are exhausted (give-up scenario).
    - Spans annotate attempts with attributes: `retry.attempt`, `retry.final_attempts`, `retry.give_up`, and scheduled backoff (`retry.scheduled_backoff`). When OpenTelemetry not installed, these no-op gracefully.
    - A temporary shim preserves monkeypatched `resilient_post` / `resilient_get` across module reloads to maintain backward compatibility with legacy tests (see `network_conventions.md`).