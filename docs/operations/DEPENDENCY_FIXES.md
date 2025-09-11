---
title: Dependency and Pipeline Fixes Applied
origin: DEPENDENCY_FIXES.md (root)
status: migrated
last_moved: 2025-09-02
---

## Overview

Original root file migrated. Content preserved below.

### Dependency and Pipeline Fixes Applied

## Issues Resolved

### 1. yt-dlp Filepath Parsing ✅

**Problem**: Code was looking for `filepath` field, but yt-dlp outputs `_filename` and `filename`
**Solution**: Updated `src/ultimate_discord_intelligence_bot/tools/yt_dlp_download_tool.py` to check multiple possible filepath fields:

```python
local_path = (
    info.get("filepath") or
    info.get("_filename") or
    info.get("filename")
)
```

### 2. Missing ffmpeg Dependency ✅

**Problem**: `ERROR: Postprocessing: ffmpeg not found`
**Solution**:

- Added doctor checks in the unified setup wizard to verify ffmpeg presence and suggest install steps
- Created `install_dependencies.sh` script for easy system dependency installation
- Added clear installation instructions for different operating systems

### 3. Missing Impersonation Dependencies ✅

**Problem**: `WARNING: no impersonate target is available`
**Solution**:

- Added `curl-cffi>=0.5.0` to `pyproject.toml` dependencies
- Documented optional installation flow via pip
- Added graceful handling if installation fails (optional dependency)

## Files Modified

1. **`src/ultimate_discord_intelligence_bot/tools/yt_dlp_download_tool.py`**
   - Enhanced filepath extraction to handle yt-dlp's actual output format
   - Now checks `filepath`, `_filename`, and `filename` fields in order

2. **`pyproject.toml`**
   - Added `curl-cffi>=0.5.0` for impersonation support

3. **Setup wizard**
   - `doctor` validates ffmpeg and highlights missing optional tools
   - Guides users to fix environment before running

4. **`install_dependencies.sh`** (NEW)
   - Cross-platform script to install system dependencies
   - Supports Linux (apt, yum, dnf, pacman), macOS (brew), Windows (manual)
   - Automatic OS detection and appropriate package manager usage

## Testing the Fixes

To test that the fixes work:

1. **Install system dependencies**:

```bash
./install_dependencies.sh
```

2. **Start the bot with the unified setup CLI**:

```bash
python -m ultimate_discord_intelligence_bot.setup_cli run discord
```

3. **Test video download**:

```bash
source venv/bin/activate
python -c "
from src.ultimate_discord_intelligence_bot.tools.yt_dlp_download_tool import YouTubeDownloadTool
tool = YouTubeDownloadTool()
result = tool.run('https://www.youtube.com/watch?v=dQw4w9WgXcQ')
print('Status:', result.get('status'))
print('Local path:', result.get('local_path'))
"
```

## Expected Behavior

After these fixes:

- ✅ yt-dlp should successfully download videos without filepath errors
- ✅ ffmpeg should handle video post-processing without errors
- ✅ Impersonation warnings should be eliminated
- ✅ The `!analyze <url>` Discord command should work end-to-end
- ✅ Video files should be correctly located for transcription and analysis

## Next Steps

1. Test the complete pipeline with a real Discord command
2. Verify that video transcription works with the correctly located files
3. Ensure the analysis results are properly formatted and sent to Discord
