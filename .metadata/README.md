# 🎯 Repository Navigation Guide

Welcome to the Ultimate Discord Intelligence Bot repository. This guide will help you navigate the cleaned and organized codebase.

## Quick Links

📋 **[CLEANUP_REPORT.md](CLEANUP_REPORT.md)** - Full cleanup & reorganization report
📁 **[DIRECTORY_INDEX.md](DIRECTORY_INDEX.md)** - Complete directory structure mapping
📝 **[CLEANUP_SUMMARY.md](CLEANUP_SUMMARY.md)** - What was cleaned and why

---

## 🚀 Quick Start

### Find a Feature
```
src/ultimate_discord_intelligence_bot/features/<feature_name>/
```

Examples:
- Rights Management: `src/ultimate_discord_intelligence_bot/features/rights_management/`
- Community Pulse: `src/ultimate_discord_intelligence_bot/features/community_pulse/`
- Guest Preparation: `src/ultimate_discord_intelligence_bot/features/guest_preparation/`

### Find a Service
```
src/ultimate_discord_intelligence_bot/services/<service_name>/
```

### Find Analysis Tools
```
src/analysis/<type>/
```

Types: `transcription/`, `vision/`, `topic/`, `nlp/`, `highlight/`, `sentiment/`, `safety/`, `deduplication/`

### Find Tests
```
tests/test_<module_name>.py
```

### Find Examples
```
examples/<service_name>_example.py
```

---

## 📁 Directory Organization

### Core Application
- **`src/ultimate_discord_intelligence_bot/`** - Main package
  - **`features/`** - ✨ Unified feature modules (NEW!)
  - **`services/`** - Core services
  - **`tools/`** - CrewAI tools
  - **`config/`** - YAML configurations
  - **`main.py`** - Entry point
  - **`crew.py`** - CrewAI crew definition

### Analysis Pipeline
- **`src/analysis/`** - Content analysis services
  - `transcription/` - ASR & diarization
  - `vision/` - Visual parsing
  - `topic/` - Topic segmentation
  - `nlp/` - NLP analysis
  - `highlight/` - Highlight detection
  - `sentiment/` - Sentiment analysis
  - `safety/` - Safety checks
  - `deduplication/` - Deduplication

### Supporting
- **`src/memory/`** - Vector storage
- **`src/mcp_server/`** - FastMCP server
- **`src/publishing/`** - Artifact publishing
- **`src/pipeline/`** - Pipeline orchestration
- **`src/ingest/`** - Content ingestion
- **`src/discord/`** - Discord integration

### Testing & Data
- **`tests/`** - Test suite
- **`data/`** - Application data
- **`crew_data/`** - Workspace data
- **`benchmarks/`** - Performance benchmarks
- **`fixtures/`** - Test fixtures

### Documentation
- **`docs/`** - Comprehensive documentation
- **`examples/`** - Usage examples
- **`reports/`** - Analysis reports

### Configuration
- **`.config/`** - Project config
- **`.metadata/`** - Navigation docs (you are here!)
- **`config/`** - YAML configs

### Development
- **`scripts/`** - Utility scripts
- **`ops/`** - Operations/deployment
- **`venv/`** - Python environment
- **`migrations/`** - Database migrations

### Archives
- **`archive/`** - Archived code, logs, old tests
  - `root_files/` - Old scripts & markdown
  - `logs/` - Historical logs
  - `json_data/` - Old JSON data

---

## 💡 Import Patterns

### New Recommended Style
```python
from ultimate_discord_intelligence_bot.features.rights_management import RightsReuseIntelligenceService
from ultimate_discord_intelligence_bot.services.memory_service import MemoryService
from ultimate_discord_intelligence_bot.tools.content_analysis import ContentAnalysisTool
```

### Legacy Style (Still Works)
```python
from features.rights_management import RightsReuseIntelligenceService  # Via wrapper
```

---

## 📊 Repository Statistics

| Metric | Value |
|--------|-------|
| Total Directories | 28 |
| Core Features | 3+ |
| Analysis Pipelines | 8+ |
| Test Modules | 50+ |
| Example Scripts | 15+ |
| Documentation Files | 50+ |

---

## 🔍 What's Where?

### Want to understand a feature?
1. Look in `src/ultimate_discord_intelligence_bot/features/<name>/`
2. Check the corresponding test in `tests/test_<name>.py`
3. See example usage in `examples/<name>_example.py`

### Want to add new feature?
1. Create directory: `src/ultimate_discord_intelligence_bot/features/<new_feature>/`
2. Add implementation files
3. Create tests in `tests/test_<new_feature>.py`
4. Add example in `examples/<new_feature>_example.py`

### Want to modify analysis pipeline?
1. Find service in `src/analysis/<type>/`
2. Update implementation
3. Update tests in `tests/`
4. Update example in `examples/`

---

## 🧹 Cleanup Summary

Recent cleanup (2025-10-17):
- ✅ Removed build artifacts (21M+ freed)
- ✅ Unified feature modules
- ✅ Archived old root files
- ✅ Organized configuration
- ✅ Maintained backward compatibility

See **[CLEANUP_REPORT.md](CLEANUP_REPORT.md)** for details.

---

## 📚 Documentation Structure

All documentation files in `.metadata/`:
- **README.md** - This file
- **CLEANUP_REPORT.md** - Full cleanup report
- **DIRECTORY_INDEX.md** - Directory structure
- **CLEANUP_SUMMARY.md** - What was cleaned

---

## 🎯 Next Steps

1. ✅ Repository structure is organized
2. ✅ Feature modules are unified
3. ✅ Documentation is in place
4. 🚀 Ready for development!

### Recommendations
- Use new import paths for new code
- Gradually update legacy imports
- Keep `.metadata/` docs current
- Archive experimental code properly

---

**Last Updated:** October 17, 2025
**Status:** 🟢 Ready for Development
