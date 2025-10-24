# /autointel Performance Issues & Solutions

## Issues Identified

### 1. Discord Interaction Token Expiry ❌ CRITICAL

**Problem:** Discord interaction tokens expire after 15 minutes, but `/autointel` workflow took 31 minutes (1867 seconds).

**Error:**

```
ERROR: 401 Unauthorized (error code: 50027): Invalid Webhook Token
```

**Impact:**

- Progress updates fail after 15 minutes
- Final results can't be sent to Discord
- User sees incomplete/no response

**Solutions:**

#### Option A: Early Response with Status Link (RECOMMENDED)

Respond within 15 minutes with a status link, then continue processing:

```python
# After initial deferral, send early status message within 10 minutes
async def send_early_status(interaction, workflow_id: str):
    """Send early status message before token expiry."""
    status_link = f"https://yourapp.com/status/{workflow_id}"
    await interaction.followup.send(
        f"🔄 Analysis in progress (this may take 20-30 minutes).\n"
        f"Track progress: {status_link}\n"
        f"Results will be posted to this channel when complete.",
        ephemeral=False
    )
```

#### Option B: Webhook Fallback

Switch to channel webhooks after 10 minutes:

```python
# Store channel webhook for long-running tasks
async def get_channel_webhook(channel):
    """Get or create webhook for channel."""
    webhooks = await channel.webhooks()
    for webhook in webhooks:
        if webhook.name == "AutoIntel Bot":
            return webhook
    return await channel.create_webhook(name="AutoIntel Bot")

# Use webhook instead of interaction.followup after 10 minutes
webhook_url = await get_channel_webhook(interaction.channel)
await webhook.send(content=results, username="AutoIntel Bot")
```

#### Option C: Orphaned Results Handler (ALREADY IMPLEMENTED)

The code already has `persist_workflow_results()` - enable notifications:

```bash
export ENABLE_ORPHANED_RESULT_NOTIFICATIONS=1
export ORPHANED_RESULTS_CHECK_INTERVAL=300  # Check every 5 minutes
```

---

### 2. PostHog Telemetry Errors ⚠️ NON-CRITICAL

**Problem:** CrewAI is trying to send analytics to PostHog (us.i.posthog.com) but connection is refused.

**Error:**

```
WARNING:urllib3.connectionpool:Retrying... Connection refused to us.i.posthog.com:443
ERROR:backoff:Giving up send_request(...) after 4 tries
```

**Impact:**

- Noisy logs (hundreds of warnings)
- Slight performance overhead from retry attempts
- No functional impact (telemetry only)

**Solutions:**

#### Option A: Disable PostHog in CrewAI (RECOMMENDED)

```bash
# Add to .env
export CREWAI_DISABLE_TELEMETRY=1
export TELEMETRY_OPT_OUT=1
```

#### Option B: Configure PostHog Proxy (if you want telemetry)

```bash
export POSTHOG_HOST="https://your-proxy.com"
export POSTHOG_API_KEY="your-key"
```

#### Option C: Suppress Warnings in Logging

```python
# In logging configuration
import logging
logging.getLogger("urllib3.connectionpool").setLevel(logging.ERROR)
logging.getLogger("backoff").setLevel(logging.ERROR)
```

---

### 3. Long Execution Time ⏱️ 31 Minutes

**Problem:** Workflow took 1867 seconds (~31 minutes) for a single video analysis.

**Breakdown (estimated):**

- Download: ~1-2 minutes
- Transcription: ~5-10 minutes
- Analysis (serial tasks): ~15-20 minutes
- Memory operations: ~3-5 minutes
- Network overhead: ~2-5 minutes

**Solutions:**

#### Enable Parallel Execution (if not already enabled)

```bash
export ENABLE_PARALLEL_MEMORY_OPS=1
export ENABLE_PARALLEL_ANALYSIS=1
export ENABLE_PARALLEL_FACT_CHECKING=1
```

#### Use Faster Models

```bash
export OPENAI_MODEL_NAME="gpt-4o-mini"  # Faster, cheaper
export ENABLE_PROMPT_COMPRESSION=1      # Reduce token count
```

#### Cache Transcriptions

```bash
export ENABLE_GPTCACHE=1
export ENABLE_SEMANTIC_CACHE_SHADOW=1
```

#### Skip Optional Stages

Modify crew builder to skip non-essential stages for faster runs:

- Disable verification stage for trusted sources
- Skip social monitoring for one-off analyses
- Reduce memory operation depth

---

## Recommended Configuration

### For Production Discord Bot

```bash
# .env additions

# Disable telemetry noise
CREWAI_DISABLE_TELEMETRY=1
TELEMETRY_OPT_OUT=1

# Enable orphaned result notifications
ENABLE_ORPHANED_RESULT_NOTIFICATIONS=1
ORPHANED_RESULTS_CHECK_INTERVAL=300

# Performance optimizations
ENABLE_PARALLEL_MEMORY_OPS=1
ENABLE_PARALLEL_ANALYSIS=1
ENABLE_PARALLEL_FACT_CHECKING=1
ENABLE_PROMPT_COMPRESSION=1

# Use faster models for speed-critical stages
OPENAI_MODEL_NAME=gpt-4o-mini

# Suppress verbose logging
LOG_LEVEL=INFO
```

### Code Changes Needed

**1. Early Status Response (discord_helpers.py)**

Add timer to send status before token expiry:

```python
async def _execute_with_early_status(
    interaction: discord.Interaction,
    workflow_id: str,
    execute_fn: Callable,
    timeout_minutes: int = 10
):
    """Execute long-running workflow with early status message."""
    
    # Schedule early status message
    async def send_early_status():
        await asyncio.sleep(timeout_minutes * 60)
        try:
            await interaction.followup.send(
                f"⏳ Still processing workflow {workflow_id}...\n"
                f"This is taking longer than expected.\n"
                f"Results will be posted when complete.",
                ephemeral=False
            )
        except Exception as e:
            logger.warning(f"Could not send early status: {e}")
    
    # Run both concurrently
    status_task = asyncio.create_task(send_early_status())
    
    try:
        result = await execute_fn()
        status_task.cancel()  # Cancel status if we finish early
        return result
    except Exception as e:
        status_task.cancel()
        raise
```

**2. Webhook Fallback (autonomous_orchestrator.py)**

```python
async def _get_fallback_webhook(self, interaction):
    """Get channel webhook for fallback after token expiry."""
    if not hasattr(interaction, 'channel'):
        return None
        
    try:
        webhooks = await interaction.channel.webhooks()
        for webhook in webhooks:
            if webhook.name == "AutoIntel Fallback":
                return webhook
        return await interaction.channel.create_webhook(
            name="AutoIntel Fallback",
            reason="Long-running /autointel results"
        )
    except Exception as e:
        self.logger.error(f"Could not create fallback webhook: {e}")
        return None
```

---

## Quick Fix Commands

### 1. Suppress PostHog Errors NOW

```bash
# Add to your current .env
echo "CREWAI_DISABLE_TELEMETRY=1" >> .env
echo "TELEMETRY_OPT_OUT=1" >> .env
```

### 2. Enable Parallel Execution

```bash
# Add to .env
echo "ENABLE_PARALLEL_MEMORY_OPS=1" >> .env
echo "ENABLE_PARALLEL_ANALYSIS=1" >> .env
echo "ENABLE_PARALLEL_FACT_CHECKING=1" >> .env
```

### 3. Test with Faster Settings

```bash
export OPENAI_MODEL_NAME=gpt-4o-mini
export ENABLE_PROMPT_COMPRESSION=1
export CREWAI_DISABLE_TELEMETRY=1

# Run test
python -m ultimate_discord_intelligence_bot.setup_cli run discord
```

---

## Monitoring & Debugging

### Check Workflow Duration

```python
# In autonomous_orchestrator.py, add timing metrics
start_time = time.time()
result = await self._execute_intelligence_workflow(...)
duration = time.time() - start_time

self.logger.info(f"✅ Workflow completed in {duration:.2f}s ({duration/60:.1f}m)")

# Alert if too long
if duration > 900:  # 15 minutes
    self.logger.warning(f"⚠️ Workflow exceeded Discord token limit: {duration:.2f}s")
```

### Enable Timing Breakdown

```bash
export ENABLE_CREW_STEP_VERBOSE=1
export CREWAI_SAVE_TRACES=1
export CREWAI_TRACES_DIR=crew_data/Logs/traces
```

Then analyze traces:

```bash
python scripts/analyze_crew_traces.py --traces-dir crew_data/Logs/traces
```

---

## See Also

- [docs/crewai_integration.md](../crewai_integration.md) - CrewAI configuration
- [docs/operations/CONTRIBUTING.md](CONTRIBUTING.md) - Performance guidelines
- [Discord Interaction Limits](https://discord.com/developers/docs/interactions/receiving-and-responding#interaction-response-object-interaction-callback-type) - Official docs
