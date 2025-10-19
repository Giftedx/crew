# Week 4 Hybrid Pilot Deployment Guide

**Status**: Ready to deploy  
**Recommendation**: Option 3 (Hybrid Pilot - 48 hour test)  
**Configuration**: Quality 0.55, Early Exit 0.70 (tuned and validated)

---

## Quick Start

### Prerequisites

1. **Discord Test Server**: You need a Discord server for the 48-hour pilot
2. **Server ID**: Enable Developer Mode in Discord → Right-click server → Copy ID
3. **Bot Token**: Ensure `DISCORD_BOT_TOKEN` is set in `.env`
4. **Database**: Qdrant/vector store configured (or using in-memory)

### One-Command Deployment

```bash
# Set your test server ID
export DISCORD_GUILD_ID=YOUR_SERVER_ID_HERE

# Deploy pilot (runs for 48 hours)
python scripts/deploy_week4_pilot.py
```

---

## What This Does

The pilot deployment:

1. ✅ Configures tuned Week 4 thresholds (quality 0.55, exit 0.70)
2. ✅ Limits bot to single test server (via `DISCORD_GUILD_ID`)
3. ✅ Enables all optimizations (quality filtering, early exit, content routing)
4. ✅ Activates dashboard metrics collection
5. ✅ Monitors for 48 hours collecting real-world data
6. ✅ Generates deployment recommendation based on metrics

---

## Step-by-Step Instructions

### Step 1: Get Discord Server ID

1. Open Discord
2. Enable Developer Mode:
   - User Settings → Advanced → Developer Mode (toggle ON)
3. Right-click your test server
4. Select "Copy ID"
5. Save this ID - you'll need it

### Step 2: Start the Pilot

```bash
# Option A: Using environment variable (recommended)
export DISCORD_GUILD_ID=1234567890123456789  # Your server ID
python scripts/deploy_week4_pilot.py

# Option B: Using command line argument
python scripts/deploy_week4_pilot.py --guild-id 1234567890123456789

# Option C: Custom duration (e.g., 24 hours for faster testing)
python scripts/deploy_week4_pilot.py --duration 24
```

### Step 3: Start Discord Bot

In a **separate terminal**:

```bash
# The pilot script sets up monitoring, but you need to start the bot
python -m ultimate_discord_intelligence_bot.setup_cli run discord
```

The bot will now:

- Only respond to commands in your test server
- Use tuned Week 4 thresholds
- Collect metrics on all pipeline runs

### Step 4: Start Dashboard (Optional but Recommended)

In **another terminal**:

```bash
# Start the metrics dashboard
uvicorn server.app:create_app --factory --port 8000 --reload
```

Access dashboard at: <http://localhost:8000/dashboard>

### Step 5: Monitor Progress

**During the 48-hour pilot:**

- Use the bot normally in your test server
- Share various content types (videos, articles, discussions)
- Monitor dashboard for real-time metrics
- Check activation rates hourly

**What to look for:**

- Quality bypass activating on simple content (15-30% ideal)
- Early exit triggering on straightforward analysis (10-25% ideal)
- Time savings accumulating (15-25% average target)
- Quality scores staying high (≥ 0.70 required)

### Step 6: Review Results

After 48 hours (or press Ctrl+C to stop early):

```bash
# The script automatically generates a report
# Results saved to: benchmarks/week4_pilot_metrics_TIMESTAMP.json

# View summary
cat benchmarks/week4_pilot_metrics_*.json | jq .summary
```

---

## Understanding the Metrics

### Key Metrics Explained

| Metric | Target Range | What It Means |
|--------|-------------|---------------|
| **Bypass Rate** | 15-30% | % of content that skipped quality analysis (simple/low-quality) |
| **Exit Rate** | 10-25% | % of content that exited analysis early (straightforward) |
| **Time Savings** | ≥15% | Average % reduction in processing time |
| **Quality Score** | ≥0.70 | Average output quality (non-negotiable minimum) |

### Deployment Decision Matrix

The script auto-generates a recommendation:

| Recommendation | Meaning | Action |
|----------------|---------|--------|
| **DEPLOY_TO_PRODUCTION** | All metrics in target ranges | ✅ Deploy to all servers immediately |
| **DEPLOY_WITH_MONITORING** | Most metrics good | ✅ Deploy but monitor closely for 7 days |
| **CONTINUE_TUNING** | Some metrics need adjustment | ⚠️ Adjust thresholds and re-run pilot |
| **INVESTIGATE** | Metrics below expectations | ❌ Review logs and investigate issues |
| **DO_NOT_DEPLOY** | Quality too low | ❌ Quality degraded - do not deploy |

---

## Example Pilot Session

```bash
# Terminal 1: Start pilot monitoring
export DISCORD_GUILD_ID=1234567890123456789
python scripts/deploy_week4_pilot.py

# Output:
# ======================================================================
# Week 4 HYBRID PILOT DEPLOYMENT
# ======================================================================
#
# 📍 Target Server: 1234567890123456789
# ⏰ Duration: 48 hours
#
# 🔧 Configuration:
#    DISCORD_GUILD_ID=1234567890123456789
#    QUALITY_MIN_OVERALL=0.55
#    ENABLE_QUALITY_FILTERING=1
#    ENABLE_EARLY_EXIT=1
#    ENABLE_CONTENT_ROUTING=1
#    ENABLE_DASHBOARD_METRICS=1
# ...

# Terminal 2: Start Discord bot
python -m ultimate_discord_intelligence_bot.setup_cli run discord

# Terminal 3: Start dashboard
uvicorn server.app:create_app --factory --port 8000 --reload

# Then use bot normally in test server for 48 hours...
```

---

## Advanced Options

### Custom Duration

```bash
# 24-hour pilot (faster results, less data)
python scripts/deploy_week4_pilot.py --duration 24

# 72-hour pilot (more data, more confidence)
python scripts/deploy_week4_pilot.py --duration 72
```

### Custom Output Directory

```bash
# Save metrics to specific directory
python scripts/deploy_week4_pilot.py --output-dir /path/to/metrics
```

### Manual Metrics Check

```bash
# During pilot, check dashboard API
curl http://localhost:8000/api/metrics/week4_summary | jq .

# Example response:
# {
#   "bypass_rate": "22%",
#   "exit_rate": "18%", 
#   "avg_time_savings": "23%",
#   "avg_quality_score": 0.74,
#   "recommendation": "DEPLOY_TO_PRODUCTION"
# }
```

---

## Troubleshooting

### Bot not responding in test server

**Issue**: Bot responds in other servers but not the pilot server

**Solution**:

```bash
# Verify DISCORD_GUILD_ID is set correctly
echo $DISCORD_GUILD_ID

# Check bot logs for guild_id filtering
tail -f logs/discord_bot.log | grep -i guild
```

### Low activation rates (< 5%)

**Issue**: Bypass and exit rates very low after 12+ hours

**Possible causes**:

1. Content being tested is all high-quality (like validation video)
2. Thresholds still too conservative for your content mix
3. Not enough diverse content tested

**Solution**:

```bash
# Test with deliberately diverse content:
# - Share some amateur videos (low quality)
# - Share short clips (simple content)  
# - Share educational videos (routing optimization)
# - Share complex discussions (baseline comparison)
```

### Quality score dropping below 0.70

**Issue**: Average quality falling below acceptable threshold

**Immediate action**:

```bash
# STOP the pilot immediately
# Press Ctrl+C in the monitoring terminal

# Review which content triggered low quality
cat benchmarks/week4_pilot_metrics_*.json | jq '.detailed_metrics[] | select(.result.quality_score < 0.70)'

# Likely need to raise quality threshold back to 0.60 or 0.65
```

### Dashboard not updating

**Issue**: Dashboard shows no Week 4 metrics

**Solution**:

```bash
# Verify dashboard is configured for Week 4 metrics
curl http://localhost:8000/api/health

# Check if ENABLE_DASHBOARD_METRICS is set
env | grep DASHBOARD

# Restart dashboard server
pkill -f "uvicorn.*server.app"
uvicorn server.app:create_app --factory --port 8000 --reload
```

---

## After the Pilot

### If Metrics Are Good (Deploy to Production)

```bash
# 1. Update production .env with tuned config
cat >> .env.production << EOF
QUALITY_MIN_OVERALL=0.55
ENABLE_QUALITY_FILTERING=1
ENABLE_EARLY_EXIT=1
ENABLE_CONTENT_ROUTING=1
ENABLE_DASHBOARD_METRICS=1
EOF

# 2. Remove guild restriction (deploy to all servers)
# Remove or comment out DISCORD_GUILD_ID in .env

# 3. Deploy to production
python -m ultimate_discord_intelligence_bot.setup_cli run discord

# 4. Monitor production dashboard for first 7 days
open http://your-production-server:8000/dashboard
```

### If Metrics Need Tuning

```bash
# Example: Lower quality threshold more aggressively
export QUALITY_MIN_OVERALL=0.50  # Was 0.55

# Re-run pilot with adjusted config
python scripts/deploy_week4_pilot.py --duration 24
```

### If Quality Degraded (Do Not Deploy)

```bash
# Raise quality threshold back up
export QUALITY_MIN_OVERALL=0.60  # Was 0.55

# Or disable quality filtering entirely
export ENABLE_QUALITY_FILTERING=0

# Focus on early exit and routing optimizations only
python scripts/deploy_week4_pilot.py --duration 24
```

---

## Configuration Reference

### Environment Variables

```bash
# Required
DISCORD_GUILD_ID=<test_server_id>    # Limits bot to test server
DISCORD_BOT_TOKEN=<token>             # Your bot token

# Week 4 Tuned Configuration
QUALITY_MIN_OVERALL=0.55              # Tuned from 0.65
ENABLE_QUALITY_FILTERING=1            # Quality bypass optimization
ENABLE_EARLY_EXIT=1                   # Early termination optimization  
ENABLE_CONTENT_ROUTING=1              # Content-type routing optimization
ENABLE_DASHBOARD_METRICS=1            # Metrics collection

# Optional (from config/early_exit.yaml)
# min_exit_confidence: 0.70            # Tuned from 0.80
```

### Files Modified/Created

- `config/early_exit.yaml` - min_exit_confidence: 0.70
- `scripts/deploy_week4_pilot.py` - This deployment script
- `benchmarks/week4_pilot_metrics_*.json` - Pilot results

---

## Expected Outcomes

### Optimistic Scenario (≥65% of runs show optimization)

- Bypass rate: 20-30%
- Exit rate: 15-25%
- Time savings: 20-30%
- Quality: 0.72-0.80
- **Recommendation**: DEPLOY_TO_PRODUCTION ✅

### Realistic Scenario (40-65% of runs show optimization)

- Bypass rate: 15-22%
- Exit rate: 10-18%  
- Time savings: 15-23%
- Quality: 0.70-0.75
- **Recommendation**: DEPLOY_WITH_MONITORING ✅

### Below Expectations (<40% optimization)

- Bypass rate: <15%
- Exit rate: <10%
- Time savings: <15%
- Quality: Variable
- **Recommendation**: CONTINUE_TUNING or INVESTIGATE ⚠️

---

## Support

### Documentation References

- Full analysis: `WEEK4_TUNED_VALIDATION_ANALYSIS.md`
- Deployment options: `WEEK4_NEXT_STEPS.md`
- Current status: `WHERE_WE_ARE_NOW.md`
- Diagnostic tool: `scripts/diagnose_week4_optimizations.py`

### Next Steps Based on Results

1. **Success (≥15% savings, quality ≥0.70)**: Deploy to production
2. **Partial Success (10-15% savings)**: Deploy with extended monitoring
3. **Below Target (<10% savings)**: Review content mix or adjust thresholds
4. **Quality Issues (<0.70)**: Raise thresholds or disable specific optimizations

---

**Ready to deploy?** Run `python scripts/deploy_week4_pilot.py` to start your 48-hour pilot! 🚀
