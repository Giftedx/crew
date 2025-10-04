# Week 3 Days 2-3: Individual Phase Testing Execution Guide

**Date:** January 5, 2025  
**Status:** 🚧 **IN PROGRESS** - Ready to execute  
**Phase:** Phase 3 Performance Optimization, Week 3 (Validation)  
**Days:** 2-3 (Individual phase testing)

---

## Executive Summary

This guide provides step-by-step instructions for executing Week 3 Days 2-3 validation testing. The goal is to run **Combinations 1-4** (sequential baseline + 3 individual optimizations) with **3 iterations each** to measure actual performance savings vs expected.

### What We're Testing

| Combination | Name | Flags Enabled | Expected Savings | Iterations | Est. Time |
|-------------|------|---------------|------------------|------------|-----------|
| **1** | Sequential Baseline | None | 0 min (baseline) | 3 | ~31.5 min |
| **2** | Memory Only | PARALLEL_MEMORY_OPS | 0.5-1 min | 3 | ~28.5-30 min |
| **3** | Analysis Only | PARALLEL_ANALYSIS | 1-2 min | 3 | ~25.5-28.5 min |
| **4** | Fact-Checking Only | PARALLEL_FACT_CHECKING | 0.5-1 min | 3 | ~28.5-30 min |

**Total Estimated Time:** 2-3 hours for all 12 runs (4 combinations × 3 iterations)

---

## Prerequisites

### 1. Environment Setup

Ensure you have all required dependencies installed:

```bash
# Verify Python environment
python --version  # Should be 3.11+

# Check if orchestrator can be imported
python -c "from ultimate_discord_intelligence_bot.autonomous_orchestrator import AutonomousIntelligenceOrchestrator; print('✅ Orchestrator import successful')"

# Verify CrewAI installation
python -c "from crewai import Crew, Task, Agent; print('✅ CrewAI import successful')"
```

### 2. Test Video Selection

Choose a YouTube video with the following characteristics:

**Recommended Properties:**
- **Length:** 5-10 minutes (not too short, not too long)
- **Content:** Educational or interview content (good for analysis)
- **Availability:** Publicly accessible (not age-restricted or geo-blocked)
- **Language:** English (for best transcription quality)

**Example URLs:**
```bash
# Example 1: TED Talk (~10 min)
URL="https://youtube.com/watch?v=8jPQjjsBbIc"

# Example 2: Educational content (~7 min)
URL="https://youtube.com/watch?v=..."

# Example 3: Interview (~8 min)
URL="https://youtube.com/watch?v=..."
```

**⚠️ IMPORTANT:** Use the **same URL** for all 12 runs to ensure fair comparison!

### 3. Required Secrets

Ensure these environment variables are set:

```bash
# Check if secrets are configured
python -c "from core.secure_config import get_config; print('OPENROUTER_API_KEY:', '✅' if get_config('OPENROUTER_API_KEY') else '❌')"

# If missing, set them
export OPENROUTER_API_KEY="your_key_here"
export OPENAI_API_KEY="your_key_here"  # If using OpenAI
export DISCORD_BOT_TOKEN="your_token_here"  # For Discord integration
```

### 4. Disk Space

Ensure you have sufficient disk space:

```bash
# Check available space
df -h /home/crew

# Benchmark outputs will consume:
# - Logs: ~100 MB (12 runs × ~8 MB per run)
# - Results JSON: ~5 MB
# - Downloaded videos: ~50-100 MB per run (cached, so ~100 MB total)
# Total: ~200-300 MB
```

---

## Execution Steps

### Step 1: Run Baseline (Combination 1)

**Goal:** Establish the sequential baseline (~10.5 min per run)

```bash
# Navigate to repo root
cd /home/crew

# Run Combination 1 only (3 iterations)
python scripts/benchmark_autointel_flags.py \
  --url "YOUR_YOUTUBE_URL_HERE" \
  --depth experimental \
  --iterations 3 \
  --combinations 1 \
  --output-dir benchmarks \
  --verbose

# Expected output:
# Combination 1 (sequential_baseline) - Iteration 1: ~629s (10.5 min)
# Combination 1 (sequential_baseline) - Iteration 2: ~629s (10.5 min)
# Combination 1 (sequential_baseline) - Iteration 3: ~629s (10.5 min)
# Mean: ~629s, Median: ~629s
```

**Success Criteria:**
- ✅ All 3 iterations complete successfully
- ✅ Mean time: 600-660 seconds (10-11 min)
- ✅ Standard deviation <30 seconds (consistent performance)
- ✅ No errors in logs

**If Baseline Fails:**
1. Check logs in `benchmarks/logs/benchmark_run_*.log`
2. Verify URL is accessible: `yt-dlp --list-formats "YOUR_URL"`
3. Check API keys are valid
4. Ensure sufficient disk space

**Expected Files Created:**
```
benchmarks/
├── logs/
│   └── benchmark_run_20250105_*.log
├── combination_1_interim.json
├── flag_validation_results_20250105_*.json
└── flag_validation_summary_20250105_*.md
```

---

### Step 2: Run Individual Optimizations (Combinations 2-4)

**Goal:** Measure individual phase savings vs baseline

```bash
# Run Combination 2 (Memory Only)
python scripts/benchmark_autointel_flags.py \
  --url "YOUR_YOUTUBE_URL_HERE" \
  --depth experimental \
  --iterations 3 \
  --combinations 2 \
  --output-dir benchmarks \
  --verbose

# Expected: Mean ~599-609s (9.5-10 min) = 0.5-1 min savings vs baseline

# Run Combination 3 (Analysis Only)
python scripts/benchmark_autointel_flags.py \
  --url "YOUR_YOUTUBE_URL_HERE" \
  --depth experimental \
  --iterations 3 \
  --combinations 3 \
  --output-dir benchmarks \
  --verbose

# Expected: Mean ~569-589s (8.5-9.5 min) = 1-2 min savings vs baseline

# Run Combination 4 (Fact-Checking Only)
python scripts/benchmark_autointel_flags.py \
  --url "YOUR_YOUTUBE_URL_HERE" \
  --depth experimental \
  --iterations 3 \
  --combinations 4 \
  --output-dir benchmarks \
  --verbose

# Expected: Mean ~599-609s (9.5-10 min) = 0.5-1 min savings vs baseline
```

**Alternative: Run All at Once**

```bash
# Run Combinations 1-4 in one command (takes 2-3 hours)
python scripts/benchmark_autointel_flags.py \
  --url "YOUR_YOUTUBE_URL_HERE" \
  --depth experimental \
  --iterations 3 \
  --combinations 1 2 3 4 \
  --output-dir benchmarks \
  --verbose
```

---

### Step 3: Monitor Execution

**Real-time Monitoring:**

```bash
# In a separate terminal, tail the log
tail -f benchmarks/logs/benchmark_run_*.log

# Watch interim results
watch -n 10 "cat benchmarks/combination_*_interim.json | jq '.[-1].timing'"

# Monitor system resources
htop  # Check CPU/memory usage
```

**Expected Log Output:**

```
2025-01-05 10:00:00 [INFO] Running Combination 1 (sequential_baseline) - Iteration 1
2025-01-05 10:00:00 [INFO]   Starting execution at 2025-01-05T10:00:00
[... orchestrator logs ...]
2025-01-05 10:10:29 [INFO]   Completed in 629.45s (10.49 min)

2025-01-05 10:10:29 [INFO] Running Combination 1 (sequential_baseline) - Iteration 2
[...]
```

**Warning Signs to Watch For:**
- ⚠️ Duration >12 min (720s) → Performance regression
- ⚠️ Errors in logs → Check API keys, network, disk space
- ⚠️ High variance (std >60s) → Inconsistent performance, may need more iterations

---

## Data Collection & Analysis

### Automated Analysis

The benchmark script automatically generates:

1. **JSON Results** (`flag_validation_results_*.json`):
   - Full timing data for all runs
   - Quality metrics (if available)
   - Flag configurations
   - Error information

2. **Summary Report** (`flag_validation_summary_*.md`):
   - Summary table with actual vs expected savings
   - Statistical analysis (mean, median, std)
   - Pass/fail status for each combination

**Example Summary Output:**

```markdown
## Summary Table

| Combination | Name | Mean Time | vs Baseline | Expected Savings | Actual Savings | Status |
|-------------|------|-----------|-------------|------------------|----------------|--------|
| 1 | sequential_baseline | 10.49 min | - | - | - | 📊 Baseline |
| 2 | memory_only | 9.73 min | -0.76 min | 0.5-1.0 min | 0.76 min | ✅ Pass |
| 3 | analysis_only | 9.12 min | -1.37 min | 1.0-2.0 min | 1.37 min | ✅ Pass |
| 4 | fact_checking_only | 9.89 min | -0.60 min | 0.5-1.0 min | 0.60 min | ✅ Pass |
```

### Manual Verification

**Calculate Individual Savings:**

```python
# Python script to analyze results
import json

# Load results
with open('benchmarks/flag_validation_results_*.json') as f:
    results = json.load(f)

# Calculate baseline mean
baseline_times = [r['timing']['duration_seconds'] for r in results['1']]
baseline_mean = sum(baseline_times) / len(baseline_times)

print(f"Baseline mean: {baseline_mean:.2f}s ({baseline_mean/60:.2f} min)")

# Calculate savings for each combination
for combo_id in [2, 3, 4]:
    combo_times = [r['timing']['duration_seconds'] for r in results[str(combo_id)]]
    combo_mean = sum(combo_times) / len(combo_times)
    savings = baseline_mean - combo_mean
    
    print(f"Combination {combo_id}: {combo_mean:.2f}s ({combo_mean/60:.2f} min)")
    print(f"  Savings: {savings:.2f}s ({savings/60:.2f} min)")
```

---

## Success Criteria

### ✅ Must-Have Criteria

1. **Baseline Established**
   - Combination 1 completes 3 iterations successfully
   - Mean time: 600-660 seconds (10-11 min)
   - Standard deviation <30 seconds

2. **Individual Optimizations Pass**
   - Combination 2: 0.5-1 min savings (memory ops)
   - Combination 3: 1-2 min savings (analysis)
   - Combination 4: 0.5-1 min savings (fact-checking)

3. **Quality Maintained**
   - No errors across all 12 runs
   - Consistent transcript quality
   - Graph/memory operations successful

4. **Data Integrity**
   - All results saved to JSON
   - Logs complete and readable
   - Summary report generated

### ⚠️ Nice-to-Have Criteria

- Low variance (std <20 seconds)
- Actual savings exceed expected minimum
- No performance regressions
- Sub-10-minute total for Combination 3

---

## Troubleshooting

### Issue: Runs Taking Too Long (>12 min)

**Possible Causes:**
1. Network latency (slow YouTube download)
2. API rate limiting (OpenRouter throttling)
3. Insufficient CPU/memory resources

**Solutions:**
```bash
# Check network speed
curl -o /dev/null https://youtube.com  # Should be fast

# Check API rate limits
curl -H "Authorization: Bearer $OPENROUTER_API_KEY" \
  https://openrouter.ai/api/v1/auth/key  # Check quota

# Monitor system resources
htop  # Look for CPU bottlenecks
free -h  # Check available memory
```

### Issue: Errors During Execution

**Common Errors:**
1. `ImportError: No module named 'crewai'` → Run `pip install -e '.[dev]'`
2. `KeyError: 'OPENROUTER_API_KEY'` → Set API key in `.env`
3. `yt-dlp error` → Check YouTube URL accessibility

**Debug Steps:**
```bash
# Test orchestrator import
python -c "from ultimate_discord_intelligence_bot.autonomous_orchestrator import AutonomousIntelligenceOrchestrator; print('OK')"

# Test YouTube URL
yt-dlp --list-formats "YOUR_URL"

# Check logs for full traceback
cat benchmarks/logs/benchmark_run_*.log | grep -A 20 "ERROR"
```

### Issue: Inconsistent Results (High Variance)

**Possible Causes:**
1. Different video caching states
2. API response time variance
3. System load fluctuations

**Solutions:**
- Run more iterations (5 instead of 3)
- Use isolated environment (close other apps)
- Cache warm-up run before benchmarks

---

## Next Steps After Completion

### If All Tests Pass ✅

1. **Proceed to Days 4-5:** Combination testing (Combinations 5-8)
2. **Document Results:** Create `WEEK_3_DAYS_2_3_COMPLETE.md`
3. **Update Progress Tracker:** Mark Days 2-3 as complete
4. **Archive Results:** Move JSON/logs to permanent storage

### If Tests Fail ❌

1. **Analyze Root Cause:** Review logs, check error patterns
2. **Adjust Expectations:** Update expected savings if needed
3. **Extend Testing:** Add more iterations for statistical confidence
4. **Report Issues:** Document failures in `WEEK_3_ISSUES.md`

---

## Estimated Timeline

| Activity | Duration | Details |
|----------|----------|---------|
| **Setup** | 15 min | Environment checks, URL selection, secret verification |
| **Combination 1 (Baseline)** | 35 min | 3 iterations × ~10.5 min + overhead |
| **Combination 2 (Memory)** | 32 min | 3 iterations × ~10 min + overhead |
| **Combination 3 (Analysis)** | 29 min | 3 iterations × ~9 min + overhead |
| **Combination 4 (Fact-Checking)** | 32 min | 3 iterations × ~10 min + overhead |
| **Analysis & Documentation** | 20 min | Generate reports, verify results |
| **TOTAL** | **2.5-3 hours** | All 12 runs + setup + analysis |

---

## Quick Reference Commands

```bash
# Full Days 2-3 execution (all combinations)
python scripts/benchmark_autointel_flags.py \
  --url "YOUR_URL" \
  --depth experimental \
  --iterations 3 \
  --combinations 1 2 3 4 \
  --output-dir benchmarks \
  --verbose

# Quick test (1 iteration, combinations 1 and 3 only)
python scripts/benchmark_autointel_flags.py \
  --url "YOUR_URL" \
  --iterations 1 \
  --combinations 1 3 \
  --output-dir benchmarks

# View results summary
cat benchmarks/flag_validation_summary_*.md

# Analyze JSON results
python -c "
import json
with open('benchmarks/flag_validation_results_*.json') as f:
    data = json.load(f)
    for combo_id, results in data.items():
        times = [r['timing']['duration_minutes'] for r in results if r['success']]
        print(f'Combo {combo_id}: {sum(times)/len(times):.2f} min avg')
"
```

---

## Checklist

### Pre-Execution ☑️

- [ ] Python 3.11+ installed
- [ ] Dependencies installed (`pip install -e '.[dev]'`)
- [ ] Orchestrator imports successfully
- [ ] Test video URL selected (5-10 min, public, English)
- [ ] API keys configured (OPENROUTER_API_KEY, OPENAI_API_KEY)
- [ ] Disk space available (300+ MB)
- [ ] Benchmark script executable (`chmod +x scripts/benchmark_autointel_flags.py`)

### During Execution ☑️

- [ ] Combination 1 (Baseline) completed (3 iterations)
- [ ] Combination 2 (Memory) completed (3 iterations)
- [ ] Combination 3 (Analysis) completed (3 iterations)
- [ ] Combination 4 (Fact-Checking) completed (3 iterations)
- [ ] All runs successful (no errors)
- [ ] Logs captured in `benchmarks/logs/`
- [ ] Interim results saved (JSON files)

### Post-Execution ☑️

- [ ] Summary report generated (`flag_validation_summary_*.md`)
- [ ] Results analyzed (actual vs expected savings)
- [ ] Success criteria met (all combinations pass)
- [ ] Quality metrics verified (no degradation)
- [ ] Documentation updated (`WEEK_3_DAYS_2_3_COMPLETE.md`)
- [ ] Progress tracker updated (PERFORMANCE_OPTIMIZATION_PLAN.md)
- [ ] Git commit created with results

---

**Ready to Execute?** ✅

Start with:
```bash
python scripts/benchmark_autointel_flags.py --url "YOUR_URL" --combinations 1 --iterations 3 --verbose
```

Good luck! 🚀
