---
title: Discord Bot Test Commands
origin: test_commands.md (root)
status: migrated
last_moved: 2025-09-02
---

## 🧪 Test Commands for Your Discord Bot

## 🎯 Quick Tests to Try Right Now

Go to your Discord server and try these commands to verify everything is working:

### 1. Basic Functionality Tests

```text
!status
!help_full
```

### 2. Built-in Fact-Checking (No API Keys Required)

```text
!factcheck The Earth is round
!factcheck The Earth is flat
!factcheck Vaccines cause autism
!factcheck Climate change is real
```

### 3. Logical Fallacy Detection

```text
!fallacy Everyone believes this so it must be true
!fallacy You're wrong because you're stupid  
!fallacy If we allow this, next thing you know the world will end
!fallacy This is true because my friend told me
```

### 4. Content Analysis (Requires Internet)

```text
!analyze https://www.youtube.com/watch?v=dQw4w9WgXcQ
!download https://www.youtube.com/watch?v=dQw4w9WgXcQ
```

---

## 📊 Expected Results

### Status Command

Should show:

```text
🟢 Full Discord Intelligence Bot Status:
• Pipeline Tool: ✅
• Debate Tool: ✅  
• Fact Check Tool: ✅ (or ⚠️ with warning)
• Fallacy Tool: ✅
• YouTube Tool: ✅
```

### Fact-Checking Examples

- "The Earth is round" → ✅ True (99% confidence)
- "The Earth is flat" → ❌ False (95% confidence)
- "Vaccines cause autism" → ❌ False (99% confidence)
- Custom claims → 🟡 Uncertain (requires verification)

### Fallacy Detection Examples

- "Everyone believes this" → Appeal to Popularity
- "You're wrong because you're stupid" → Ad Hominem  
- "If we allow this, world will end" → Slippery Slope
- Clean arguments → ✅ No fallacies detected

---

## 🛠️ If Commands Don't Work

### Bot Not Responding

1. Check bot is online (green circle next to name)
2. Restart: `python -m ultimate_discord_intelligence_bot.setup_cli run discord`
3. Check permissions in Discord server settings

### Commands Show Errors

1. Make sure you're using `!` prefix (not `/`)
2. Check bot has "Send Messages" permission
3. Try `!status` first to verify basic functionality

### Analysis Commands Fail

1. External APIs may require paid subscriptions
2. Built-in fact-checking works without any APIs
3. Video analysis needs internet connection

---

## 🎉 Success Indicators

✅ `!status` returns bot status  
✅ `!factcheck` provides verdicts with confidence scores  
✅ `!fallacy` detects logical fallacies with explanations  
✅ `!analyze` processes video content (with valid URLs)  
✅ Error handling shows helpful messages instead of crashes

---

## 💡 Pro Tips

- Use built-in fact-checking for reliable results without API keys
- Test fallacy detection with obviously flawed arguments  
- Start with simple commands (`!status`) then try advanced ones
- Check console output for detailed error information
- Built-in patterns cover common conspiracy theories and scientific facts

Your bot is now working with comprehensive functionality even without external API subscriptions!
