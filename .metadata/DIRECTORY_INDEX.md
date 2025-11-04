# Repository Directory Index

## Core Application (`src/ultimate_discord_intelligence_bot/`)

### Main Package Structure
```
ultimate_discord_intelligence_bot/
├── __init__.py                    # Package root with lazy feature loading
├── settings.py                    # Global configuration
├── step_result.py                 # Standard result format
├── features/                      # UNIFIED FEATURE MODULES
│   ├── rights_management/         # Rights and Reuse Intelligence
│   ├── community_pulse/           # Community Pulse Analyzer
│   ├── guest_preparation/         # Guest/Topic Pre-Briefs
│   ├── sponsor_assistant/         # Sponsor & Compliance Assistant
│   ├── narrative_tracker/         # Cross-Platform Narrative Tracker
│   ├── smart_clip_composer/       # Smart Clip Composer
│   ├── claim_verifier/            # Claim and Context Verifier
│   └── knowledge_ops/             # Cross-Team Knowledge Ops
├── services/                      # Core services
├── tools/                         # CrewAI tools
├── config/                        # YAML configurations
│   ├── agents.yaml
│   └── tasks.yaml
└── ...
```

### Analysis Pipeline (`src/analysis/`)
```
analysis/
├── transcription/                 # ASR & Speaker Diarization
├── vision/                        # Visual parsing & OCR
├── topic/                         # Topic segmentation
├── nlp/                           # Claim & quote extraction
├── highlight/                     # Highlight detection
├── sentiment/                     # Sentiment & stance analysis
├── safety/                        # Safety & brand suitability
└── deduplication/                 # Cross-platform deduplication
```

### Supporting Packages
- `src/memory/` - Vector storage & embeddings
- `src/mcp_server/` - FastMCP server & tools
- `src/publishing/` - Artifact publishing
- `src/pipeline/` - Multimodal pipeline orchestration
- `src/ingest/` - Content ingestion
- `src/discord/` - Discord bot integration

## Project Organization

### Configuration & Metadata
- `.config/` - Project configuration files (pyproject.toml, requirements, etc.)
- `.metadata/` - Documentation index and cleanup summaries
- `config/` - YAML config files (policies, deprecations, etc.)

### Testing & Data
- `tests/` - Unit & integration tests
- `data/` - SQLite databases, manifests
- `crew_data/` - Crew workspace data
- `benchmarks/` - Performance benchmarks & results
- `fixtures/` - Test fixtures

### Documentation & Examples
- `docs/` - Comprehensive documentation
- `examples/` - Usage examples
- `reports/` - Analysis & reports

### Development & Operations
- `scripts/` - Development utilities
- `ops/` - Deployment & monitoring
- `profiling/` - Performance profiling data
- `venv/` - Python virtual environment
- `migrations/` - Database migrations

### Data & Services
- `cache/` - Semantic & HTTP cache
- `data/` - Application data
- `dashboards/` - Grafana/monitoring configs
- `tenants/` - Multi-tenancy config
- `baselines/` - Golden baseline data
- `datasets/` - Training/evaluation datasets

### Temporary & Historical
- `archive/` - Archived code, logs, old tests
- `profiling/` - Performance profiling
- `test_cache/` - Test cache data
- `test_graph_memory/` - Graph memory tests
- `test_hipporag_memory/` - HippoRAG memory tests
- `yt-dlp/` - YouTube-dl archives
- `pilot_metrics/` - Pilot program metrics

## Key Files

### Application Entry Points
- `src/ultimate_discord_intelligence_bot/main.py` - Main orchestrator
- `src/ultimate_discord_intelligence_bot/crew.py` - CrewAI crew definition

### Configuration
- `pyproject.toml` - Project metadata & dependencies
- `requirements.lock` - Locked dependencies
- `config/deprecations.yaml` - Deprecation tracking
- `config/feature_flags.yaml` - Feature flag definitions

### Quality Assurance
- `mypy.ini` - Type checking configuration
- `pytest.ini` - Testing configuration
- `.config/conftest.py` - Test fixtures

## Path Resolution

When looking for functionality:

1. **Feature Implementation**: `src/ultimate_discord_intelligence_bot/features/<feature_name>/`
2. **Analysis Services**: `src/analysis/<service_type>/`
3. **Core Services**: `src/ultimate_discord_intelligence_bot/services/`
4. **CrewAI Tools**: `src/ultimate_discord_intelligence_bot/tools/`
5. **Examples**: `examples/<service_name>_example.py`
6. **Tests**: `tests/test_<module_name>.py`

## Import Conventions

### Preferred (New)
```python
from ultimate_discord_intelligence_bot.features.rights_management import RightsReuseIntelligenceService
```

### Supported (Legacy)
```python
from features.rights_management import RightsReuseIntelligenceService
```

Both work due to backward-compatible wrappers.
