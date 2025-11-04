# Phase 2 Production Deployment Guide

**Version**: 1.0
**Date**: January 6, 2025
**Status**: Ready for Production
**Prerequisites**: Phase 1 + Phase 2 Weeks 1-3 complete

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Quick Start](#quick-start)
4. [Detailed Deployment](#detailed-deployment)
5. [Configuration](#configuration)
6. [Monitoring](#monitoring)
7. [Troubleshooting](#troubleshooting)
8. [Week 4 Tuning Plan](#week-4-tuning-plan)

---

## 🎯 Overview

This guide covers deploying the complete Phase 2 optimization stack, which includes:

- **Phase 1**: Quality Filtering (45-60% time reduction)
- **Week 1**: Content Type Routing (+15-25% reduction)
- **Week 2**: Early Exit Conditions (+20-25% reduction)
- **Week 3**: Performance Dashboard (real-time monitoring)

**Combined Expected Impact**: **65-80% total time reduction**

### Architecture Overview

```
Input URL
    ↓
[Download] → Post-Download Checkpoint (5% exit)
    ↓
[Transcription] → Post-Transcription Checkpoint (15% exit)
    ↓
[Quality Assessment] → Content Routing Decision
    ↓                        ↓
[Quality Bypass 60%]    [Continue Full Processing]
    ↓                        ↓
[Lightweight]         Post-Quality Checkpoint (30% exit)
    ↓                        ↓
[Memory Storage]      [Analysis + Perspective + Fallacy]
    ↓                        ↓
[Dashboard Record]    Post-Analysis Checkpoint (10% exit)
    ↓                        ↓
[Complete]            [Full Memory + Graph + Discord]
                             ↓
                      [Dashboard Record]
                             ↓
                      [Complete]
```

---

## ✅ Prerequisites

### System Requirements

- **Python**: 3.11 or higher
- **Memory**: 4GB minimum (8GB recommended)
- **Storage**: 10GB minimum
- **Network**: Stable internet for API calls

### Dependencies

```bash
# Install all required packages
pip install -e '.[dev,metrics]'

# Verify installation
python -m ultimate_discord_intelligence_bot.setup_cli doctor
```

### Required Secrets

Set these in `.env` or environment:

```bash
# Core secrets
DISCORD_BOT_TOKEN=your_discord_token
OPENAI_API_KEY=your_openai_key  # or OPENROUTER_API_KEY

# Optional (recommended for production)
QDRANT_URL=http://localhost:6333  # Vector store
GOOGLE_DRIVE_CREDENTIALS=path/to/credentials.json  # Drive upload
```

### Verify Phase 1 + Week 1-3 Code

```bash
# Check all files exist
ls -la config/quality_filtering.yaml
ls -la config/content_routing.yaml
ls -la config/early_exit.yaml
ls -la config/monitoring.yaml

# Verify server components
ls -la src/server/routers/performance_dashboard.py
ls -la src/server/static/performance_dashboard.html

# Run tests
make test-fast
```

---

## 🚀 Quick Start

### Option 1: Enable All Features (Recommended)

```bash
# Set all feature flags
export ENABLE_QUALITY_FILTERING=1
export ENABLE_CONTENT_ROUTING=1
export ENABLE_EARLY_EXIT=1
export ENABLE_DASHBOARD_METRICS=1

# Start dashboard server (in one terminal)
uvicorn server.app:create_app --factory --host 0.0.0.0 --port 8000 &

# Start Discord bot (in another terminal)
python -m ultimate_discord_intelligence_bot.setup_cli run discord
```

### Option 2: Gradual Rollout

```bash
# Week 1: Enable quality filtering only
export ENABLE_QUALITY_FILTERING=1
python -m ultimate_discord_intelligence_bot.setup_cli run discord

# After 24h: Add content routing
export ENABLE_CONTENT_ROUTING=1

# After 48h: Add early exit
export ENABLE_EARLY_EXIT=1

# After 72h: Add dashboard
export ENABLE_DASHBOARD_METRICS=1
uvicorn server.app:create_app --factory --port 8000 &
```

### Access Dashboard

```
http://localhost:8000/dashboard
```

---

## 🔧 Detailed Deployment

### Step 1: Configuration Review

Review and customize configuration files based on your needs:

#### Quality Filtering (`config/quality_filtering.yaml`)

```yaml
thresholds:
  min_overall: 0.65  # Adjust based on Week 4 data
  min_coherence: 0.60
  min_completeness: 0.60
  min_informativeness: 0.60
```

**Tuning Tips**:

- Lower `min_overall` (0.60) for more aggressive bypassing
- Raise `min_overall` (0.70) for conservative filtering
- Monitor dashboard quality score trends

#### Content Routing (`config/content_routing.yaml`)

```yaml
content_types:
  discussion:
    priority: high
    processing_mode: full  # Always full processing
  entertainment:
    priority: low
    processing_mode: lightweight  # Always bypass
  news:
    priority: medium
    processing_mode: quality_check  # Bypass if low quality
```

**Tuning Tips**:

- Adjust `processing_mode` per content type
- Add custom types in `custom_types` section
- Monitor content type bypass rates in dashboard

#### Early Exit (`config/early_exit.yaml`)

```yaml
checkpoints:
  post_download:
    min_confidence: 0.85  # High confidence for early exits
    conditions:
      - "duration_seconds < 60"  # Skip very short videos
  post_quality_filtering:
    min_confidence: 0.75  # Lower confidence after quality check
    conditions:
      - "overall_quality < 0.50"  # Exit if very low quality
```

**Tuning Tips**:

- Adjust `min_confidence` per checkpoint
- Add/remove exit conditions
- Monitor checkpoint exit rates in dashboard

### Step 2: Environment Configuration

Create/update `.env`:

```bash
# Core Features
ENABLE_QUALITY_FILTERING=1
ENABLE_CONTENT_ROUTING=1
ENABLE_EARLY_EXIT=1
ENABLE_DASHBOARD_METRICS=1

# Dashboard Configuration
DASHBOARD_API_URL=http://localhost:8000

# Quality Thresholds (override config file)
QUALITY_MIN_OVERALL=0.65
QUALITY_MIN_COHERENCE=0.60

# Logging
LOG_LEVEL=INFO
ENABLE_AUDIT_LOGGING=1

# Performance
ENABLE_SEMANTIC_CACHE=1
ENABLE_HTTP_RETRY=1
RETRY_MAX_ATTEMPTS=3

# Optional Features
ENABLE_GRAPH_MEMORY=1
ENABLE_HIPPORAG_MEMORY=1
ENABLE_PROMPT_COMPRESSION=1
```

### Step 3: Start Services

#### Terminal 1: Dashboard Server

```bash
cd /home/crew

# Production mode
uvicorn server.app:create_app \
  --factory \
  --host 0.0.0.0 \
  --port 8000 \
  --workers 2 \
  --log-level info

# Development mode (auto-reload)
uvicorn server.app:create_app \
  --factory \
  --reload \
  --port 8000
```

#### Terminal 2: Discord Bot

```bash
cd /home/crew

# Standard mode
python -m ultimate_discord_intelligence_bot.setup_cli run discord

# With enhanced features
make run-discord-enhanced
```

#### Terminal 3: Monitor Dashboard

```bash
# Open in browser
open http://localhost:8000/dashboard

# Or monitor via curl
watch -n 30 'curl -s http://localhost:8000/api/performance/metrics/summary | jq'
```

### Step 4: Verification

#### Check Dashboard API

```bash
# Test all endpoints
curl http://localhost:8000/api/performance/
curl http://localhost:8000/api/performance/metrics/summary
curl http://localhost:8000/api/performance/content-types
curl http://localhost:8000/api/performance/checkpoints
curl http://localhost:8000/api/performance/quality-trends?hours=24
```

#### Test Pipeline

```bash
# Run a test URL through the pipeline
# Watch logs for processing type (full/lightweight/early_exit)
grep "processing_type" logs/*.log

# Check dashboard for recorded metric
curl http://localhost:8000/api/performance/metrics/summary
```

#### Monitor Logs

```bash
# Follow logs
tail -f logs/*.log

# Filter for optimization events
grep -E "quality_filtering|content_routing|early_exit" logs/*.log

# Check for errors
grep ERROR logs/*.log
```

---

## ⚙️ Configuration

### Feature Flags Reference

| Flag | Default | Description |
|------|---------|-------------|
| `ENABLE_QUALITY_FILTERING` | 0 | Enable Phase 1 quality bypass |
| `ENABLE_CONTENT_ROUTING` | 0 | Enable Week 1 content type routing |
| `ENABLE_EARLY_EXIT` | 0 | Enable Week 2 checkpoint early exit |
| `ENABLE_DASHBOARD_METRICS` | 0 | Enable Week 3 dashboard recording |
| `DASHBOARD_API_URL` | `http://localhost:8000` | Dashboard API endpoint |
| `QUALITY_MIN_OVERALL` | 0.65 | Override quality threshold |
| `ENABLE_SEMANTIC_CACHE` | 0 | Enable LLM response caching |
| `ENABLE_GRAPH_MEMORY` | 0 | Enable graph-based memory |
| `ENABLE_HIPPORAG_MEMORY` | 0 | Enable HippoRAG memory |

### Configuration Files

| File | Purpose | Key Settings |
|------|---------|--------------|
| `config/quality_filtering.yaml` | Quality thresholds | `min_overall`, `min_coherence`, etc. |
| `config/content_routing.yaml` | Content type rules | `processing_mode` per type |
| `config/early_exit.yaml` | Checkpoint conditions | `min_confidence`, exit rules |
| `config/monitoring.yaml` | Alert thresholds | Bypass rate, quality targets |

### Threshold Tuning Matrix

| Scenario | Quality Min | Early Exit Confidence | Expected Bypass | Expected Quality |
|----------|-------------|----------------------|-----------------|------------------|
| **Conservative** | 0.70 | 0.85 | 50% | 0.80 |
| **Balanced** (default) | 0.65 | 0.80 | 60% | 0.75 |
| **Aggressive** | 0.60 | 0.75 | 70% | 0.70 |

---

## 📊 Monitoring

### Dashboard Metrics

Access at `http://localhost:8000/dashboard`:

- **Overall Metrics**: Total processed, bypass rate, time savings
- **Processing Breakdown**: Quality bypassed, early exits, full processing
- **Content Types**: Per-type bypass rates and quality scores
- **Checkpoints**: Exit counts, rates, top reasons
- **Quality Trends**: Time-series quality metrics

### Key Metrics to Monitor

#### Bypass Rate

- **Target**: 60% (Phase 1 + Week 1 + Week 2 combined)
- **Warning**: < 50% or > 80%
- **Action**: Adjust quality thresholds if out of range

#### Quality Score

- **Target**: 0.75 average
- **Warning**: < 0.70
- **Critical**: < 0.65
- **Action**: Increase `min_overall` if degrading

#### Early Exit Rate

- **Target**: 40% of non-bypassed content
- **Warning**: < 30% or > 60%
- **Action**: Adjust checkpoint confidence thresholds

#### Time Savings

- **Target**: 70% average
- **Warning**: < 60%
- **Action**: Review bypass and exit rates

### Alert Rules (see `config/monitoring.yaml`)

```yaml
overall_metrics:
  bypass_rate:
    target: 0.60
    warning_low: 0.50
    critical_low: 0.40
  quality_score_avg:
    target: 0.75
    warning_low: 0.70
    critical_low: 0.65
```

### Logging

```bash
# Enable detailed logging
export LOG_LEVEL=DEBUG
export ENABLE_AUDIT_LOGGING=1

# Log locations
logs/discord_bot.log  # Bot events
logs/pipeline.log     # Pipeline processing
logs/dashboard.log    # Dashboard API
```

---

## 🔍 Troubleshooting

### Dashboard Not Recording Metrics

**Symptoms**:

- Total processed = 0
- No content types shown
- No checkpoint data

**Diagnosis**:

```bash
# Check flag is set
echo $ENABLE_DASHBOARD_METRICS

# Check dashboard API is running
curl http://localhost:8000/api/performance/metrics/summary

# Check logs for recording errors
grep "dashboard" logs/*.log
```

**Solution**:

```bash
export ENABLE_DASHBOARD_METRICS=1
export DASHBOARD_API_URL=http://localhost:8000

# Restart bot
python -m ultimate_discord_intelligence_bot.setup_cli run discord
```

### Bypass Rate Too Low

**Symptoms**:

- Bypass rate < 50%
- Most content going through full processing
- Low time savings

**Diagnosis**:

```bash
# Check quality filtering is enabled
echo $ENABLE_QUALITY_FILTERING

# Check threshold
grep "min_overall" config/quality_filtering.yaml

# Check content routing
grep "processing_mode" config/content_routing.yaml
```

**Solution**:

```yaml
# In config/quality_filtering.yaml
thresholds:
  min_overall: 0.60  # Lower threshold (was 0.65)

# In config/content_routing.yaml
default_routing:
  default_mode: quality_check  # Was "full"
```

### Quality Score Degrading

**Symptoms**:

- Quality score < 0.70
- Dashboard shows red alert
- User complaints about output quality

**Diagnosis**:

```bash
# Check content type distribution
curl http://localhost:8000/api/performance/content-types | jq

# Check which types are being bypassed
grep "lightweight" logs/pipeline.log | wc -l
```

**Solution**:

```yaml
# In config/quality_filtering.yaml
thresholds:
  min_overall: 0.70  # Raise threshold (was 0.65)

# In config/content_routing.yaml
content_types:
  entertainment:
    processing_mode: full  # Was "lightweight"
```

### Early Exits Not Working

**Symptoms**:

- Early exit rate = 0%
- All non-bypassed going to full processing
- No checkpoint analytics data

**Diagnosis**:

```bash
# Check flag
echo $ENABLE_EARLY_EXIT

# Check config loaded
grep "post_download" config/early_exit.yaml

# Check logs
grep "early_exit" logs/pipeline.log
```

**Solution**:

```bash
export ENABLE_EARLY_EXIT=1

# Restart bot
python -m ultimate_discord_intelligence_bot.setup_cli run discord
```

### Dashboard API Errors

**Symptoms**:

- 500 errors on dashboard
- POST /api/performance/record failing
- Metrics not updating

**Diagnosis**:

```bash
# Check server logs
tail -f logs/dashboard.log

# Test endpoint manually
curl -X POST "http://localhost:8000/api/performance/record?processing_type=full&time_saved_pct=0.0"
```

**Solution**:

```bash
# Restart dashboard server
pkill -f uvicorn
uvicorn server.app:create_app --factory --port 8000
```

---

## 📅 Week 4 Tuning Plan

### Days 1-2: Data Collection

**Goal**: Collect 48 hours of production baseline metrics

**Actions**:

1. Deploy with all features enabled
2. Run normal workload
3. Monitor dashboard every 6 hours
4. Export metrics snapshots

**Success Criteria**:

- ✅ 100+ items processed
- ✅ 3+ content types observed
- ✅ All checkpoints tested
- ✅ No critical errors

**Export Metrics**:

```bash
# Every 6 hours, save snapshot
curl http://localhost:8000/api/performance/ > metrics_$(date +%Y%m%d_%H%M).json
```

### Days 3-4: Threshold Tuning

**Goal**: Optimize thresholds based on collected data

**Analysis**:

```bash
# Analyze metrics
cd benchmarks
python analyze_metrics.py --input metrics_*.json

# Generate recommendations
python recommend_thresholds.py
```

**Tuning Process**:

1. Review content type bypass rates
2. Adjust `min_overall` if needed
3. Review checkpoint exit rates
4. Adjust `min_confidence` per checkpoint
5. Test changes with sample URLs
6. Deploy and monitor for 12h
7. Iterate if needed

**Example Adjustments**:

```yaml
# Before (conservative)
thresholds:
  min_overall: 0.70
checkpoints:
  post_quality_filtering:
    min_confidence: 0.85

# After (balanced based on data)
thresholds:
  min_overall: 0.65  # Increased bypass rate
checkpoints:
  post_quality_filtering:
    min_confidence: 0.80  # More exits
```

### Day 5: A/B Testing

**Goal**: Validate optimal configuration

**Setup**:

```bash
# Group A: Conservative (50% of traffic)
export QUALITY_MIN_OVERALL=0.70
export CONFIG_VERSION=conservative

# Group B: Aggressive (50% of traffic)
export QUALITY_MIN_OVERALL=0.60
export CONFIG_VERSION=aggressive

# Run both in parallel, compare results
```

**Comparison Metrics**:

- Time savings difference
- Quality score difference
- User satisfaction (if tracked)
- Error rate

**Decision Criteria**:

- If quality_diff < 0.05 AND time_savings_diff > 0.05: Choose aggressive
- If quality_diff > 0.05: Choose conservative
- Else: Choose balanced

### Day 6: Documentation

**Goal**: Document optimal production settings

**Deliverables**:

1. **optimal_config.yaml**: Final tuned configuration
2. **deployment_guide.md**: Updated with findings
3. **troubleshooting_runbooks.md**: Common issues and fixes
4. **monitoring_playbook.md**: Alert response procedures

### Day 7: Alert Configuration

**Goal**: Set up production monitoring alerts

**Implementation**:

```python
# In server/routers/performance_dashboard.py
# Add alert checking logic

def check_alerts(metrics):
    alerts = []
    if metrics.bypass_rate < 0.50:
        alerts.append({
            "severity": "warning",
            "message": "Bypass rate below target (50%)"
        })
    if metrics.avg_quality_score < 0.70:
        alerts.append({
            "severity": "critical",
            "message": "Quality score below threshold (0.70)"
        })
    return alerts
```

**Alert Channels**:

- Dashboard UI indicators (red/yellow/green)
- Log warnings
- Slack notifications (optional)
- Discord notifications (optional)

---

## 📈 Expected Results

### Performance Impact

| Metric | Before Optimization | After Optimization | Improvement |
|--------|--------------------|--------------------|-------------|
| Avg Processing Time | 600s (10 min) | 180s (3 min) | **70%** ⬇️ |
| API Calls | 100% | 40% | **60%** ⬇️ |
| Quality Score | 0.78 | 0.75 | **-3.8%** ⬇️ |
| Bypass Rate | 0% | 60% | **60%** ⬆️ |
| Early Exit Rate | 0% | 40% | **40%** ⬆️ |

### Cost Savings

- **Infrastructure**: $0 (algorithmic optimization)
- **API Costs**: ~60% reduction
- **Processing Time**: ~70% reduction
- **ROI**: Immediate (no deployment cost)

### Success Criteria

- ✅ Bypass rate: 55-75%
- ✅ Quality score: > 0.70
- ✅ Time savings: > 60%
- ✅ Error rate: < 1%
- ✅ Uptime: > 99%

---

## 🎉 Summary

This deployment guide provides everything needed to deploy Phase 2 optimizations to production:

1. **Quick Start**: Enable all features in 5 minutes
2. **Detailed Steps**: Comprehensive deployment process
3. **Configuration**: Tuning guidance and examples
4. **Monitoring**: Dashboard usage and alert rules
5. **Troubleshooting**: Common issues and solutions
6. **Week 4 Plan**: Data-driven tuning process

**Expected Outcome**: **65-80% time reduction** while maintaining quality > 0.70

**Next Steps**:

1. Review prerequisites
2. Choose deployment option (quick vs gradual)
3. Start services
4. Monitor dashboard
5. Execute Week 4 tuning plan

For questions or issues, refer to troubleshooting section or review logs.

**Good luck with your deployment! 🚀**
