---
title: Root Documentation Relocation Index
origin: generated
status: active
last_updated: 2025-09-03
---

## Overview

This index tracks the migration of root-level documentation files to their new structured locations under `docs/`. All migrations are now **complete**.

## Migration Status: ✅ COMPLETE

All root-level markdown files have been successfully migrated to appropriate subdirectories with proper front matter and metadata.

| Original File | New Location | Category | Status |
|---------------|--------------|----------|--------|
| AGENTS.md | docs/agents/README.md | agents | migrated |
| ARCHITECTURE.md | docs/architecture/architecture.md | architecture | migrated |
| ARCHITECTURE_SYNC_REPORT.md | docs/architecture/sync_report_2025-09-02.md | architecture | migrated |
| PIPELINE_CONCURRENCY_ENHANCEMENT.md | docs/architecture/pipeline_concurrency_enhancement.md | architecture | migrated |
| STRATEGIC_ACTION_PLAN.md | docs/strategy/strategic_action_plan.md | strategy | migrated |
| LEGACY_REFACTORING_STRATEGY.md | docs/strategy/legacy_refactoring_strategy.md | strategy | migrated |
| IMPLEMENTATION_ROADMAP.md | docs/roadmap/implementation_roadmap.md | roadmap | migrated |
| FUTURE_WORK.md | docs/roadmap/future_work.md | roadmap | migrated |
| AI_ENHANCEMENT_IMPLEMENTATION_SUMMARY.md | docs/history/ai_enhancement_implementation_summary.md | history | migrated |
| CODEBASE_AUDIT.md | docs/operations/CODEBASE_AUDIT.md | operations | migrated |
| DEPENDENCY_FIXES.md | docs/operations/DEPENDENCY_FIXES.md | operations | migrated |
| MERGE_REPORT.md | docs/operations/MERGE_REPORT.md | operations | migrated |
| CHANGELOG.md | docs/operations/CHANGELOG.md | operations | migrated |
| CONTRIBUTING.md | docs/operations/CONTRIBUTING.md | operations | migrated |
| CLAUDE.md | docs/dev_assistants.md | dev-tools | migrated |
| GEMINI.md | docs/dev_assistants.md | dev-tools | migrated |
| SECURITY_SECRETS.md | docs/security/SECURITY_SECRETS.md | security | migrated |
| test_commands.md | docs/testing/DISCORD_TEST_COMMANDS.md | testing | migrated |

## Directory Structure

```text
docs/
├── agents/           # Agent and repository guidelines
├── architecture/     # System architecture and design
├── types_and_stubs.md # Type checking & stub strategy
├── dev_assistants.md # AI assistant guidance (consolidated)
├── history/          # Historical docs and implementation summaries
├── operations/       # Development workflow and operations
├── roadmap/          # Future planning and roadmaps
├── security/         # Security policies and procedures
├── strategy/         # Strategic planning documents
└── testing/          # Testing guides and procedures
```

## Migration Details

- **Front Matter**: All migrated files include standardized metadata (title, origin, status, last_moved)
- **Content Preservation**: Full original content maintained with no data loss
- **Link Updates**: External references should be updated to use new paths
- **Cleanup**: Root directory is now minimal and focused on core project files

## Next Steps

- Update any external documentation links to point to new locations
- Consider adding redirects if this repository is published with web hosting
- The root directory cleanup is now complete

## Newly Added Optimization Docs

The following optimization-focused documents have been added post-migration and live alongside existing performance and memory materials:

| Topic | Location | Summary |
|-------|----------|---------|
| Prompt Compression | `docs/prompt_compression.md` | Multi-pass whitespace / duplication / summarisation pipeline with metrics (`prompt_compression_ratio`). |
| Semantic Cache Prefetch | `docs/semantic_cache.md` | Similarity-based response reuse with prefetch issued/used counters and similarity histogram. |

Cross-links to these topics have been (or will be) added to `memory.md` and `rag.md` for discoverability.

---
Generated: 2025-09-03 | Migration completed successfully
