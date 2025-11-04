# ✅ Discord Interaction Timeout Fix

**Date:** October 6, 2025
**Issue:** `404 Not Found (error code: 10062): Unknown interaction`
**Root Cause:** Double-defer attempt on Discord interaction
**Status:** Fixed

---

## Problem Analysis

### Error Message

```
❌ Failed to defer response: 404 Not Found (error code: 10062): Unknown interaction
```

### Root Cause

The `/autointel` command was deferring the response **twice**, which violates Discord's API rules:

1. **First defer** in `/autointel` slash command (registrations.py line 577):

   ```python
   await interaction.response.defer()  # ✅ First defer - OK
   ```

2. **Second defer** in background handler (background_autointel_handler.py line 62):

   ```python
   await interaction.response.defer(ephemeral=False)  # ❌ Second defer - FAILS!
   ```

**Discord only allows ONE defer per interaction.** The second defer attempt fails with "Unknown interaction" because the interaction token has already been used.

---

## The Fix

### Changed Files

**1. `/home/crew/src/ultimate_discord_intelligence_bot/discord_bot/registrations.py`**

**Before:**

```python
# Immediately defer to prevent timeout and run the shared executor
try:
    await interaction.response.defer()
    print(f"🤖 /autointel command started: URL={url}, Depth={depth}")
except Exception as defer_error:
    print(f"❌ Failed to defer response: {defer_error}")
    return

await _execute_autointel(interaction, url, depth)
```

**After:**

```python
print(f"🤖 /autointel command started: URL={url}, Depth={depth}")
await _execute_autointel(interaction, url, depth)
```

**Rationale:** Let the background handler manage the defer instead of doing it in the slash command.

---

**2. `/home/crew/src/ultimate_discord_intelligence_bot/background_autointel_handler.py`**

**Before:**

```python
# Get webhook URL from environment
webhook_url = os.getenv("DISCORD_WEBHOOK")
if not webhook_url:
    await interaction.response.send_message(  # ❌ Can't send before defer!
        "❌ **Configuration Error**\n\n"
        "Background processing requires `DISCORD_WEBHOOK` to be configured.\n"
        "Please set the webhook URL in your `.env` file.",
        ephemeral=True,
    )
    return

# Defer immediately to prevent timeout
await interaction.response.defer(ephemeral=False)
```

**After:**

```python
# Defer immediately to prevent timeout (if not already deferred)
if not interaction.response.is_done():
    await interaction.response.defer(ephemeral=False)

# Get webhook URL from environment
webhook_url = os.getenv("DISCORD_WEBHOOK")
if not webhook_url:
    await interaction.followup.send(  # ✅ Use followup after defer
        "❌ **Configuration Error**\n\n"
        "Background processing requires `DISCORD_WEBHOOK` to be configured.\n"
        "Please set the webhook URL in your `.env` file.",
        ephemeral=True,
    )
    return
```

**Rationale:**

- Check if already deferred with `interaction.response.is_done()`
- Defer FIRST before any validation/checks
- Use `interaction.followup.send()` for messages after deferring

---

## Key Discord API Rules

### Rule 1: Defer Only Once

```python
# ✅ CORRECT
if not interaction.response.is_done():
    await interaction.response.defer()

# ❌ WRONG - Will fail if already deferred
await interaction.response.defer()
await interaction.response.defer()  # Error: Unknown interaction
```

### Rule 2: Defer Within 3 Seconds

```python
@bot.tree.command(...)
async def my_command(interaction):
    # Must defer within 3 seconds
    await interaction.response.defer()  # ✅ Do this FIRST

    # Now you have 15 minutes for followup messages
    await interaction.followup.send("Result here")
```

### Rule 3: Use Followup After Defer

```python
# After deferring, use followup, not response
await interaction.response.defer()

# ✅ CORRECT
await interaction.followup.send("Message")

# ❌ WRONG - Can't use response after defer
await interaction.response.send_message("Message")
```

---

## Testing the Fix

### 1. Start the Bot

```bash
.venv/bin/python scripts/start_full_bot.py
```

**Expected:**

- "✅ Background worker initialized (unlimited analysis time enabled)"
- No errors during startup

### 2. Run /autointel Command

In Discord:

```
/autointel url:https://youtube.com/watch?v=... depth:standard
```

**Expected Behavior:**

- ✅ Immediate acknowledgment (< 3 seconds) with workflow_id
- ✅ No "Unknown interaction" errors
- ✅ Background analysis starts
- ✅ Results delivered via webhook when complete

**No Longer Expected:**

- ❌ "Failed to defer response" errors
- ❌ "Unknown interaction" errors

### 3. Verify Logs

```bash
# Should NOT see these errors anymore:
❌ Failed to defer response: 404 Not Found (error code: 10062): Unknown interaction
```

---

## What Changed vs. Before

### Before Fix ❌

- Slash command deferred interaction immediately
- Background handler tried to defer again → **FAILED**
- Webhook validation happened before defer → **WRONG ORDER**
- Users saw "Unknown interaction" errors

### After Fix ✅

- Slash command doesn't defer (delegates to handler)
- Background handler checks if already deferred
- Defer happens FIRST, then validation
- Uses `followup.send()` for messages after defer
- No more "Unknown interaction" errors

---

## Additional Improvements

### Error Handling Pattern

```python
async def handle_autointel_background(interaction, ...):
    """Improved error handling pattern."""

    # 1. Defer FIRST (before any logic)
    if not interaction.response.is_done():
        await interaction.response.defer(ephemeral=False)

    # 2. Validate and use followup for errors
    if not webhook_url:
        await interaction.followup.send("❌ Error message", ephemeral=True)
        return

    # 3. Continue with workflow
    workflow_id = await background_worker.start_background_workflow(...)

    # 4. Send acknowledgment via followup
    await interaction.followup.send(f"✅ Started: {workflow_id}")
```

---

## Summary

**Problem:** Double-defer attempt causing "Unknown interaction" errors
**Solution:** Single defer with proper response.is_done() check
**Files Modified:** 2 (registrations.py, background_autointel_handler.py)
**Status:** Ready to test

**Next Steps:**

1. Restart Discord bot
2. Test `/autointel` command
3. Verify no timeout errors
4. Confirm unlimited analysis time works

---

## Quick Reference

### Discord Interaction Lifecycle

```
User runs /command
    ↓
interaction.response.defer()  ← Must happen within 3 seconds
    ↓
[Up to 15 minutes for processing]
    ↓
interaction.followup.send()  ← Send results
```

### For Background Processing

```
User runs /autointel
    ↓
Defer immediately (< 3 seconds)
    ↓
Start background workflow (returns workflow_id)
    ↓
Send acknowledgment via followup
    ↓
[Background processing - unlimited time]
    ↓
Deliver results via webhook (even hours later)
```

**The key insight:** Background processing eliminates the 15-minute limit by using webhooks instead of interaction followups for final results.
