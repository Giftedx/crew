# Deprecation Dashboard

A comprehensive tool for managing and tracking deprecated features in the codebase.

## Overview

The Deprecation Dashboard provides visibility into the deprecation lifecycle, migration status, and timeline compliance. It integrates with existing deprecation validation tools to give you a complete picture of your codebase's deprecation health.

## Quick Start

```bash
# Generate a dashboard report
python scripts/deprecation_dashboard.py

# Get JSON output for automation
python scripts/deprecation_dashboard.py --format json

# Generate HTML report
python scripts/deprecation_dashboard.py --format html --output dashboard.html
```

## What It Shows

### Health Score

- Overall deprecation health (0-100)
- Based on violations, overdue items, and timeline compliance

### Migration Status

- Which deprecated features have migration scripts available
- Current migration status (pending/complete)
- Direct links to migration tools

### Timeline Tracking

- Days until removal deadlines
- Upcoming deprecation warnings
- Past-deadline violation alerts

### Actionable Recommendations

- Clear next steps for addressing issues
- Migration script execution commands
- Timeline compliance guidance

## Example Output

```text
╔══════════════════════════════════════════════════════════════════════════════╗
║                        DEPRECATION DASHBOARD                              ║
╚══════════════════════════════════════════════════════════════════════════════╝

Health Score: 🟢 100.0/100

📊 Summary:
   Total deprecated features: 2
   Critical violations: 0
   Upcoming deadlines: 2

🔧 Migration Status:
   ❌ ENABLE_ANALYSIS_HTTP_RETRY: Migrations pending
   ❌ services.learning_engine.LearningEngine: Migrations pending

💡 Recommendations:
   ⚠️  2 deprecations due within 120 days
   🔧 Run scripts/migrate_http_retry_flag.py to migrate ENABLE_ANALYSIS_HTTP_RETRY
   🔧 Run scripts/migrate_learning_engine.py to migrate services.learning_engine.LearningEngine
```

## Available Migration Scripts

| Deprecated Feature | Migration Script | Status |
|-------------------|------------------|--------|
| `ENABLE_ANALYSIS_HTTP_RETRY` | `scripts/migrate_http_retry_flag.py` | ✅ Available |
| `services.learning_engine.LearningEngine` | `scripts/migrate_learning_engine.py` | ✅ Available |

## CI/CD Integration

Integrate the dashboard into your CI/CD pipeline:

```bash
# Generate JSON report
python scripts/deprecation_dashboard.py --format json > deprecation_status.json

# Check health score
HEALTH=$(jq '.health_score' deprecation_status.json)
if (( $(echo "$HEALTH < 80" | bc -l) )); then
    echo "❌ Deprecation health too low: $HEALTH/100"
    exit 1
fi

# Check for pending migrations
PENDING=$(jq '.migration_status | map(select(.pending_migrations == true)) | length' deprecation_status.json)
if [ "$PENDING" -gt 0 ]; then
    echo "⚠️  $PENDING features have pending migrations"
fi
```

## Related Tools

- `scripts/check_deprecations.py` - Core deprecation validation
- `scripts/validate_deprecated_flags.py` - Flag-specific validation
- `config/deprecations.yaml` - Deprecation registry

## Configuration

The dashboard reads from `config/deprecations.yaml` to understand:

- Which features are deprecated
- Removal timelines
- Replacement recommendations
- Current deprecation stage

## Output Formats

### Console (Default)

Human-readable terminal output with colors and formatting.

### JSON

Machine-readable format for automation and integration:

```json
{
  "timestamp": "2025-09-03",
  "health_score": 100.0,
  "scan_results": {...},
  "migration_status": {...},
  "recommendations": [...]
}
```

### HTML

Web-viewable report with styling and tables.

## Health Score Calculation

The health score is calculated based on:

- **Critical Violations**: -30 points each (removed features still in use)
- **Overdue Items**: -20 points each (past removal deadline)
- **Base Score**: 100 points, reduced by violations

A score of 100 indicates perfect deprecation health, while lower scores indicate issues requiring attention.
