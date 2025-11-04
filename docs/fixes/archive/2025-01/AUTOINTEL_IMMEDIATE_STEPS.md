# /autointel Command - IMMEDIATE Diagnostic Steps

**Status**: 🔴 Critical failures reported
**Your Command**: `/autointel url:https://www.youtube.com/watch?v=xtFiJ8AVdW0 depth:Experimental - Cutting-Edge AI`

---

## 🚨 IMMEDIATE ACTION REQUIRED

I've just improved the logging to make failures visible. Now we need to **run the command again** to see what's actually breaking.

### Step 1: Enable Full Logging (30 seconds)

Add this to your `.env` file:

```bash
# Enable verbose logging to see what's failing
LOG_LEVEL=DEBUG
ENABLE_CREW_STEP_VERBOSE=1

# Optional: Enable experimental depth (currently disabled by default)
ENABLE_EXPERIMENTAL_DEPTH=1
```

### Step 2: Run the Discord Bot

```bash
# Terminal 1: Start the bot with verbose logging
python -m ultimate_discord_intelligence_bot.setup_cli run discord
```

**Expected Output** (look for this):

```
🚀 Starting Full Discord Intelligence Bot...
🧭 Startup mode: [mode]
```

### Step 3: Run Your Command in Discord

In your Discord channel, run:

```
/autointel url:https://www.youtube.com/watch?v=xtFiJ8AVdW0 depth:standard
```

**Note**: Start with `depth:standard` first (not experimental) - this will test fewer stages and make debugging easier.

### Step 4: Capture the Logs

Look for these **NEW WARNING MESSAGES** I just added:

```
⚠️ Analysis agent context population FAILED: [error details]
⚠️ Verification agent context population FAILED: [error details]
⚠️ [Stage] agent context population FAILED: [error details]
```

**If you see these warnings**, copy them and share them with me. They'll tell us exactly what's breaking.

**If you DON'T see these warnings**, it means context population is succeeding but something else is failing. Check for:

- Tool execution errors
- Empty data being passed to tools
- LLM/API errors

---

## 🔍 What to Look For

### Success Indicators ✅

```
✅ Stage 1 complete: Pipeline execution
✅ Stage 2 complete: Download
✅ Stage 3 complete: Pipeline full
✅ Populated shared context on N tools for agent [agent_name]
```

### Failure Indicators ❌

```
❌ ⚠️ [Agent] context population FAILED: [error]
❌ Stage [N] failed: [error]
❌ Tool execution failed: [error]
❌ CrewAI agents not available
❌ Pipeline execution failed
```

---

## 📋 Quick Diagnostic Checklist

Before running, verify:

### 1. API Keys Present?

```bash
# Check .env file
grep -E "(OPENAI_API_KEY|OPENROUTER_API_KEY)" .env | head -n 2
```

**Expected**: Should show your API keys (partially masked)

### 2. Discord Credentials?

```bash
# Check .env file
grep -E "DISCORD_BOT_TOKEN" .env | head -n 1
```

**Expected**: Should show your bot token (partially masked)

### 3. CrewAI Installed?

```bash
python -c "import crewai; print(f'CrewAI version: {crewai.__version__}')"
```

**Expected**: Should show version number (e.g., `CrewAI version: 0.x.x`)

### 4. All Dependencies?

```bash
python -m ultimate_discord_intelligence_bot.setup_cli doctor
```

**Expected**: Should show system health status

---

## 🎯 Common Failure Scenarios

### Scenario A: Context Population Failing

**Symptoms**:

```
⚠️ Analysis agent context population FAILED: 'Agent' object has no attribute 'tools'
```

**Cause**: Agent not properly initialized with tool wrappers

**Fix**: Check if `self.agent_coordinators` is populated in the orchestrator

### Scenario B: Tools Called with Empty Data

**Symptoms**:

- Analysis returns empty sentiment
- Fact checking returns "no claims"
- Memory storage stores nothing

**Cause**: Shared context not being used by CrewAI LLM

**Fix**: Requires architecture change (see AUTOINTEL_FIX_IMPLEMENTATION.md)

### Scenario C: LLM API Errors

**Symptoms**:

```
Error: Invalid API key
Error: Rate limit exceeded
Error: Model not found
```

**Fix**: Check API keys, quotas, model names

### Scenario D: Pipeline Failures

**Symptoms**:

```
Stage 3 failed: Pipeline execution error
Error downloading video
```

**Fix**: Check network, yt-dlp installation, URL validity

---

## 📤 What to Send Me

After running the command, send me:

### 1. Console Output (last 100 lines)

```bash
# Save to file
python -m ultimate_discord_intelligence_bot.setup_cli run discord 2>&1 | tail -n 100 > autointel_output.log
```

### 2. Any Warning Messages

Look for lines starting with `⚠️` and copy them

### 3. Discord Bot Response

What did the bot actually post in Discord? Did it:

- Complete successfully with results?
- Fail partway through?
- Post empty/incorrect data?

### 4. Which Stages Completed

```
Stage 1: ✅/❌
Stage 2: ✅/❌
Stage 3: ✅/❌
Stage 4: ✅/❌
Stage 5: ✅/❌
```

---

## 🔧 Emergency Workaround

If you need results NOW and can't wait for the full fix:

### Option 1: Use ContentPipeline Directly

```python
# Run this in a Python shell
from ultimate_discord_intelligence_bot.pipeline_components.orchestrator import ContentPipeline

pipeline = ContentPipeline()
result = await pipeline.process_video("https://www.youtube.com/watch?v=xtFiJ8AVdW0")

print(result.data)
```

This bypasses the autonomous orchestrator and uses the working pipeline directly.

### Option 2: Use Standard Depth Only

```
/autointel url:https://www.youtube.com/watch?v=xtFiJ8AVdW0 depth:standard
```

Standard depth (stages 1-10) has fewer failures than experimental (25 stages).

---

## 📚 Related Documentation

- **Full Analysis**: `/home/crew/AUTOINTEL_FIX_IMPLEMENTATION.md`
- **Original Issue**: `/home/crew/docs/AUTOINTEL_CRITICAL_ISSUES.md`
- **Fix Guide**: `/home/crew/docs/AUTOINTEL_FIX_GUIDE.md`

---

## ⏭️ Next Steps After Diagnosis

Once you send me the logs showing what's failing, I can:

1. **Identify the exact failure point** (which stage, which tool)
2. **Implement a targeted fix** for that specific issue
3. **Provide a working implementation** you can test immediately

**Don't spend time debugging yourself** - just run the command, capture the output, and send it to me. The new logging I added will make the failures obvious.

---

## 🆘 If Nothing Works

If the bot won't even start:

```bash
# Check Python version
python --version  # Should be 3.10-3.13

# Reinstall dependencies
pip install -e '.[dev]'

# Run minimal health check
python -c "from ultimate_discord_intelligence_bot.crew import UltimateDiscordIntelligenceBotCrew; print('OK')"
```

If that fails, we have a deeper installation issue to fix first.
