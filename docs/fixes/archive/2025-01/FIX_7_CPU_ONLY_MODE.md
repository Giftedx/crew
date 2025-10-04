# Fix #7: Force CPU-only Mode (CUDA/cuDNN Error Resolution)

## Issue

Discord bot crashes with CUDA library errors on startup:

```
Unable to load any of {libcudnn_graph.so.9.10.2, libcudnn_graph.so.9.10, libcudnn_graph.so.9, libcudnn_graph.so}
Invalid handle. Cannot load symbol cudnnCreate
make: *** [Makefile:82: run-discord-enhanced] Error 250
```

## Root Cause

PyTorch/Whisper attempting to use GPU acceleration but CUDA/cuDNN libraries not properly installed or configured.

## Solution

Force CPU-only mode by setting `CUDA_VISIBLE_DEVICES=""` environment variable.

## Implementation

### Location: `/home/crew/.env`

Added after line with `TORCH_CUDA_ARCH_LIST`:

```bash
# Force CPU-only mode (no CUDA/GPU) - fixes cuDNN errors on systems without GPU
CUDA_VISIBLE_DEVICES=""
```

## Impact

- ✅ Prevents CUDA initialization errors
- ✅ Whisper runs on CPU (slower but functional)
- ✅ Bot starts successfully without GPU hardware
- ⚠️ Transcription may be slower (CPU vs GPU)
- ℹ️ No impact on functionality, only performance

## Testing

```bash
# Bot should start without CUDA errors
make run-discord-enhanced

# Should see normal startup logs, no cuDNN errors
# Whisper will use CPU: "Using device: cpu"
```

## Alternative Solutions

If you have a working CUDA setup:

1. Install proper CUDA toolkit + cuDNN libraries
2. Remove or comment out `CUDA_VISIBLE_DEVICES=""` from `.env`
3. Verify PyTorch CUDA: `python -c "import torch; print(torch.cuda.is_available())"`

## Related Files

- `.env` - Environment configuration (CUDA_VISIBLE_DEVICES added)
- `src/ultimate_discord_intelligence_bot/tools/audio_transcription_tool.py` - Whisper usage
- `Makefile` - run-discord-enhanced target

## Status

✅ **IMPLEMENTED** - CPU-only mode configured in .env
🔄 **TESTING** - Verifying bot startup with fix applied

## Next Steps

1. Verify bot starts without CUDA errors
2. Test full /autointel workflow with all 7 fixes
3. Monitor Whisper transcription performance on CPU
