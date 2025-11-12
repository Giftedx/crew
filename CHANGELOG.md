# Changelog

All notable changes to the Ultimate Discord Intelligence Bot project will be documented in this file.

## [Unreleased] - 2025-01-04

- OpenRouter service enhancements:
  - Emergency prompt compression retry: Automatically detects token/context overflow errors (HTTP 400/413/422 with provider messages) and performs a one-time retry after aggressive prompt compression. This improves robustness for long prompts without caller changes.
  - Response quality assessment: Attaches a lightweight `quality_assessment` block to LLM results with a 0–1 score and signals (structure, apologies, length). Toggle via `ENABLE_QUALITY_ASSESSMENT` (default: enabled). No extra API calls are made.

Notes:

- The compression retry uses existing `PromptEngine.optimise_with_metadata` with `force_enable=True` and respects `provider_overrides.max_tokens` when present. If retry still fails, the original error path is preserved.
- Quality assessment is best-effort and fast; it is meant for routing/observability rather than formal evaluation.

### Security

- **CRITICAL FIX**: Added input validation to prevent Cypher injection in Neo4j store (`src/kg/neo4j/store.py`)
  - Added bounds checking for `depth` and `max_depth` parameters (1-10 range)
  - Prevents potential injection via variable-length path patterns

### Added

- **Tool Registration**: Added `RedditAPITool` and `TwitterAPITool` to tools MAPPING and **all**
- **Environment Configuration**: Added comprehensive environment variable documentation to `.env.example`
  - Reddit API credentials (`REDDIT_CLIENT_ID`, `REDDIT_CLIENT_SECRET`, `REDDIT_USER_AGENT`)
  - Twitter/X API credentials (`TWITTER_BEARER_TOKEN`, etc.)
  - Neo4j configuration (`NEO4J_URI`, `NEO4J_USER`, `NEO4J_PASSWORD`)
  - ARQ Redis queue configuration (`ARQ_REDIS_URL`)
  - Playwright web automation settings (`ENABLE_PLAYWRIGHT`, `PLAYWRIGHT_HEADLESS`, `PLAYWRIGHT_BROWSER`)
  - LlamaIndex integration settings (`LLAMAINDEX_PERSIST_DIR`, `LLAMAINDEX_CHUNK_SIZE`, `LLAMAINDEX_CHUNK_OVERLAP`)
- **Architecture Documentation**: Comprehensive architecture overview and Mermaid diagrams
- **Quality Gates**: Detailed quality gate requirements and compliance checking
- **Crew Consolidation**: Unified crew entry points with feature flag support
- **StepResult Compliance**: Automated compliance checking and reporting
- **Discord Publisher**: Flag-guarded Discord artifact publishing with tenant isolation
- **Operations Runbook**: Complete operational procedures and troubleshooting guide
- **Observability Testing**: Enhanced metrics, logging, and health monitoring tests
- **Model Spec Integration**: Complete OpenAI Model Spec compliance framework
- **Political Bias Detection**: Multi-dimensional bias analysis and measurement system
- **Governance Framework**: Comprehensive safety and fairness governance system
- **Red Line Guards**: Critical safety boundary enforcement
- **Content Safety Classification**: Four-tier content classification system
- **Bias Evaluation Dashboard**: Real-time bias monitoring and visualization
- **Agent Instruction System**: Hierarchical instruction management with conflict resolution
- **Communication Style Enforcement**: Model Spec communication principle enforcement
- **Refusal Handler**: Helpful refusal responses with clear explanations
- **Audit Trail System**: Comprehensive decision logging and monitoring
- **Governance Configuration**: YAML-based configuration management
- **Governance Testing**: Comprehensive test suite for governance framework
- **Governance Documentation**: Complete usage and integration documentation

### Changed

- **Crew Routing**: Main entry point now uses crew consolidation shim
- **Feature Flags**: Added crew consolidation flags for gradual migration
- **Configuration**: Updated configuration documentation with new flags
- **Feature Flags**: Added comprehensive governance and bias detection flags
- **StepResult**: Enhanced with PII filtering and skipped property
- **Type Hints**: Updated to modern Python syntax (| instead of Union, Optional)
- **Documentation**: Enhanced documentation with architecture diagrams and runbooks

### Technical Improvements

- **StepResult Compliance**: 52.4% compliance rate identified (target: 98%)
- **Crew Consolidation**: Single crew entry point with backward compatibility
- **Observability**: Enhanced monitoring and health check capabilities
- **Discord Integration**: Improved artifact publishing with tenant isolation
- **Documentation**: Comprehensive operational and architectural documentation
- **Ingestion Shim**: Test-focused ingestion pipeline now normalizes `published_at` values and hardens creator namespace handling

### Fixed

- **Ingestion Tests Compatibility**: Addressed unit tests expecting:
  - Creator fallback: when provider metadata lacks a channel/creator, namespace defaults to `unknown` and non-string creators are coerced to strings
  - `published_at` normalization: naive datetimes are converted to ISO 8601 with explicit UTC offset (`+00:00`); strings are preserved; `None` becomes empty string; value is attached to each upserted record payload

### Configuration Changes

- Added `ENABLE_LEGACY_CREW` flag for legacy crew support
- Added `ENABLE_CREW_MODULAR` flag for modular crew system
- Added `ENABLE_CREW_REFACTORED` flag for refactored crew system
- Added `ENABLE_CREW_NEW` flag for new crew system
- Added `ENABLE_DISCORD_PUBLISHING` flag for Discord artifact publishing
- Added `DISCORD_DRY_RUN` flag for testing Discord publishing

### Files Added

- `docs/architecture/overview.md` - System architecture documentation
- `docs/architecture/diagram.mmd` - Mermaid architecture diagram
- `docs/quality-gates.md` - Quality gate requirements and procedures
- `docs/architecture/design-note-v1.md` - Design decisions and alternatives
- `docs/runbook.md` - Operations runbook and troubleshooting guide
- `src/ultimate_discord_intelligence_bot/crew_consolidation.py` - Crew consolidation shim
- `scripts/stepresult_compliance_check.py` - StepResult compliance checker
- `scripts/test_observability.py` - Observability testing script
- `scripts/post_to_discord.py` - Discord artifact publisher

### Files Modified

- `src/ultimate_discord_intelligence_bot/main.py` - Updated to use crew consolidation
- `src/ultimate_discord_intelligence_bot/config/feature_flags.py` - Added crew consolidation flags
- `docs/configuration.md` - Updated with new feature flags
- `README.md` - Added reference to quality gates documentation

### Breaking Changes

- None (all changes are backward compatible)

### Migration Guide

1. **Crew Consolidation**: No migration required - uses canonical crew by default
1. **Feature Flags**: New flags are disabled by default
1. **Discord Publishing**: Requires `ENABLE_DISCORD_PUBLISHING=true` and webhook URL
1. **StepResult Compliance**: Existing tools continue to work, compliance improvements recommended

### Performance Impact

- **Positive**: Improved crew routing efficiency
- **Positive**: Enhanced observability and monitoring
- **Neutral**: Discord publishing only active when enabled
- **Neutral**: StepResult compliance checker is optional

### Security Considerations

- **Discord Publishing**: Requires webhook URL configuration
- **Tenant Isolation**: Maintained in all new features
- **PII Filtering**: Preserved in observability enhancements
- **Access Control**: No changes to existing security model

### Known Issues

- StepResult compliance rate is 52.4% (target: 98%)
- Some tools may need StepResult migration
- Discord publisher requires webhook configuration
- Observability tests show some minor issues with StepResult.skip attribute

### Future Improvements

- Complete StepResult compliance migration
- Enhanced observability dashboard
- Advanced Discord publishing features
- Performance optimization recommendations
- Additional crew implementation options

### Dependencies

- No new dependencies added
- Existing dependencies maintained
- Optional Discord webhook for publishing features

### Testing

- Added comprehensive observability testing
- StepResult compliance checking
- Discord publisher testing
- Crew consolidation validation
- Documentation validation

### Documentation

- Complete architecture documentation
- Operational runbook
- Quality gate procedures
- Configuration reference updates
- Design decision documentation
