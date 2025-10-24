# Session Resilience Quick Reference

## For Operators / Production Support

### What Changed?

The `/autointel` command now handles Discord session timeouts gracefully. Long-running workflows (>15 minutes) no longer crash - instead, results are saved to disk.

### How to Check for Orphaned Results

```bash
# List all orphaned workflow results
ls -la data/orphaned_results/

# View a specific result
cat data/orphaned_results/wf_1234567890.json | jq .

# Search for results by URL
grep -r "youtube.com" data/orphaned_results/

# Count orphaned results
find data/orphaned_results/ -name "*.json" | wc -l
```

### Log Messages to Watch For

**Normal Operation (Session Open):**

```
✅ Orchestrator completed successfully in 45.23s
Communication & Reporting Coordinator delivered specialized results
```

**Session Closed (New Behavior - EXPECTED):**

```
⚠️ Discord session closed before reporting results. Persisting results for workflow wf_123...
📁 Results saved to data/orphaned_results/wf_123.json
Retrieval command: /retrieve_results workflow_id:wf_123
```

**Error to Monitor:**

```
❌ Failed to persist workflow results: [error details]
```

This indicates disk/permissions issues. Check `data/orphaned_results/` directory exists and is writable.

### Metrics to Monitor

```bash
# Session closure events (expected for long workflows)
discord_session_closed_total{stage="communication_reporting"}

# Result persistence (should match session closures)
workflow_results_persisted_total{reason="session_closed"}
```

### When to Investigate

✅ **NORMAL (Don't worry):**

- Session closure logs for workflows >15 minutes
- Results persisted to disk
- No error stack traces

⚠️ **INVESTIGATE:**

- Session closure for workflows <10 minutes (unexpected)
- Failed persistence (disk/permission issues)
- Cascading RuntimeError exceptions (fix regression)

### Troubleshooting

**Problem:** Results not being persisted

```bash
# Check directory exists
mkdir -p data/orphaned_results

# Check permissions
chmod 755 data/orphaned_results

# Check disk space
df -h .
```

**Problem:** Cannot find workflow results

```bash
# Search by timestamp (last 24 hours)
find data/orphaned_results/ -name "*.json" -mtime -1

# Search by partial workflow ID
find data/orphaned_results/ -name "*123*.json"

# View all workflow IDs
jq -r '.workflow_id' data/orphaned_results/*.json
```

### Phase 2: Retrieval Command (Not Yet Implemented)

When implemented, users will be able to retrieve orphaned results:

```
/retrieve_results workflow_id:wf_1234567890
```

Until then, operators can manually extract and share results from JSON files.

### Cleanup (Manual for Now)

```bash
# Find results older than 30 days
find data/orphaned_results/ -name "*.json" -mtime +30

# Delete old results
find data/orphaned_results/ -name "*.json" -mtime +30 -delete
```

Future: Automatic cleanup will be implemented.

### Metrics Dashboard Queries

If using Prometheus/Grafana:

```promql
# Session closure rate by stage
rate(discord_session_closed_total[5m])

# Results persisted per day
sum(increase(workflow_results_persisted_total[1d]))

# Session closure percentage
(
  sum(rate(discord_session_closed_total[5m]))
  /
  sum(rate(workflow_runs_total[5m]))
) * 100
```

### Support Workflow

1. **User reports no response from /autointel**
   - Check logs for session closure
   - Look in `data/orphaned_results/` for their workflow
   - Search by URL or approximate timestamp
   - Extract and share results

2. **High rate of session closures**
   - Check if users are running very long workflows
   - Consider suggesting shorter depth settings
   - Verify Discord API is healthy

3. **Persistence failures**
   - Check disk space
   - Verify directory permissions
   - Check for filesystem errors

---

**Quick Test:**

```bash
# Verify persistence directory
mkdir -p data/orphaned_results
touch data/orphaned_results/.test
rm data/orphaned_results/.test
echo "✅ Persistence directory is writable"

# Verify orchestrator loads
python -c "from ultimate_discord_intelligence_bot.autonomous_orchestrator import AutonomousIntelligenceOrchestrator; print('✅ Orchestrator loads successfully')"

# Run tests
pytest tests/test_session_resilience.py -v
```
