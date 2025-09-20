# Local Model Selection & GPU Constraints (RTX 3070 8GB)

This document summarizes recommended open models and quantized variants for a single 8GB GPU setup. It aligns with the environment variables and scripts added in this repository.

## Goals

- Maximize reasoning & instruction quality within 8GB VRAM.
- Provide fast model switching (no full reinstall) via cached directories on a large external volume.
- Support specialized tasks (code, math) without exhausting local disk.

## Storage Layout

```text
/mnt/f/hf_cache           ← Hugging Face cache (HF_HOME, TRANSFORMERS_CACHE)
/mnt/f/models/llama3.1-8b-instruct-awq
/mnt/f/models/qwen2.5-7b-instruct-awq
/mnt/f/models/phi-3.5-mini
/mnt/f/models/mathstral-7b
/mnt/f/models/starcoder2-7b
```

## Primary Choices

| Role | Model | Rationale | Quantization |
|------|-------|-----------|--------------|
| Primary reasoning | Llama 3.1 8B Instruct | Strong balanced reasoning, broad ecosystem | AWQ 4-bit directory (future) |
| Secondary reasoning / multilingual | Qwen2.5 7B Instruct | Good multilingual & tool following | AWQ 4-bit |
| Lightweight fallback | Phi-3.5 Mini Instruct | Very fast, low VRAM, decent reasoning | Native fp16/bnb/nf4 |
| Math | Mathstral 7B | Math / STEM specialization | AWQ/GPTQ acceptable |
| Code | StarCoder2 7B | Practical coding assistance | AWQ / GPTQ |

> GPT-OSS 20B / 120B and >14B dense models are excluded due to VRAM + disk pressure.

## VRAM Strategy

- 4-bit AWQ of 7–8B models typically fits with a context window of 8k tokens on 8GB.
- If you see OOM errors: lower `VLLM_MAX_MODEL_LEN` (e.g. 4096) or reduce concurrent requests.
- For extended contexts prioritize models with native long-context support; otherwise rely on sliding window summarization.

## Scripts

### Download

```bash
./scripts/download_models.sh all      # fetch all defined models
./scripts/download_models.sh primary  # only main reasoning model
```

The script skips models already present.

### Switch Active Model

```bash
# List
python scripts/model_switcher.py --list

# Activate primary (exports VLLM_MODEL_ID)
eval "$(python scripts/model_switcher.py --set primary)"

# Activate code model directly via path or repo id
eval "$(python scripts/model_switcher.py --set /mnt/f/models/starcoder2-7b)"
```

## Environment Variables

See `.env.example` section "LOCAL MODEL STORAGE & INFERENCE". Copy to `.env` and adjust as required.

Key variables:

- `HF_HOME`, `TRANSFORMERS_CACHE`, `HF_DATASETS_CACHE` → relocate large downloads.
- `VLLM_MODEL_ID` → currently active model (overridden by switcher exports).
- `VLLM_QUANTIZATION` → hint; vLLM auto-detects when possible.

## Updating Quantized Weights

If you later obtain proper AWQ directories (e.g. from published repos or locally quantized):

1. Place them under `/mnt/f/models/<name>`.
1. Update the corresponding `*_MODEL_LOCAL` variable in `.env`.
1. Re-run the switcher.

## Troubleshooting

| Symptom | Action |
|---------|--------|
| OOM during first request | Reduce `VLLM_MAX_MODEL_LEN`; ensure no other GPU processes. |
| High cold start time | Pre-warm by running a trivial prompt after switching. |
| Disk pressure | Remove secondary/specialized model directories not in active use. |
| Wrong model loaded | Check `.active_model` file and `echo $VLLM_MODEL_ID`. |

## Future Improvements

- Add automatic AWQ quantization pipeline script.
- Add vLLM benchmark harness for latency vs. context length.
- Integrate model selection into orchestration CLI.

---

Maintainer note: keep this doc aligned with `scripts/download_models.sh` and `.env.example` whenever adding/removing models.
