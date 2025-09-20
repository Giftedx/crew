#!/usr/bin/env bash
set -euo pipefail

# Installs all optional dependency groups (extras) and performs sanity checks.
# Safe to re-run; uses pip's resolver. Assumes virtualenv already active.

EXTRAS="dev,metrics,whisper,vllm"

echo "[1/5] Installing all extras: $EXTRAS"
pip install -e ".[${EXTRAS}]"

echo "[2/5] Verifying critical imports"
python - <<'PY'
mods = ['torch','vllm','faster_whisper','whisper','prometheus_client']
failed = False
for m in mods:
    try:
        __import__(m)
        print(f"[OK] import {m}")
    except Exception as e:
        print(f"[FAIL] import {m}: {e}")
        failed = True
if failed:
    raise SystemExit(1)
PY

echo "[3/5] GPU capability check"
python - <<'PY'
import torch
print('Torch version:', torch.__version__)
print('CUDA available:', torch.cuda.is_available())
if torch.cuda.is_available():
    print('CUDA device count:', torch.cuda.device_count())
    print('Device 0 name:', torch.cuda.get_device_name(0))
PY

echo "[4/5] vLLM smoke test (no large model download)"
python - <<'PY'
from vllm.engine.arg_utils import AsyncEngineArgs
args = AsyncEngineArgs(model='facebook/opt-125m', disable_log_stats=True)
print('Constructed AsyncEngineArgs successfully.')
PY

echo "[5/5] Metrics client availability check"
python - <<'PY'
import prometheus_client
from prometheus_client import Counter
c = Counter('sample_counter_total','sample counter')
c.inc()
print('Prometheus counter inc succeeded.')
PY

echo "All extras installed and validated."

# Optional: Export autonomous-mode defaults (non-destructive). Source this script to apply.
cat <<'EOS'

Tip: To enable autonomous-mode defaults for stronger reasoning and full evaluation,
you can source these exports in your shell (they only set when unset):

    source scripts/setup_full_extras.sh && source <(cat <<'ENV'
set_default() { if [ -z "${!1}" ]; then export "$1=$2"; fi }
set_default ENABLE_HTTP_RETRY 1
set_default ENABLE_HTTP_CACHE 1
set_default ENABLE_METRICS 1
set_default ENABLE_TRACING 1
set_default ENABLE_VECTOR_SEARCH 1
set_default ENABLE_SEMANTIC_CACHE 1
set_default ENABLE_RAG_CONTEXT 1
set_default ENABLE_RETRIEVAL_ADAPTIVE_K 1
set_default ENABLE_RERANKER 1
set_default ENABLE_PROMPT_COMPRESSION 1
set_default ENABLE_PII_DETECTION 1
set_default ENABLE_RL_ROUTING 1
set_default ENABLE_RL_GLOBAL 1
set_default ENABLE_RL_CONTEXTUAL 1
set_default ENABLE_RL_THOMPSON 1
set_default ENABLE_INGEST_CONCURRENT 1
set_default ENABLE_INGEST_YOUTUBE 1
set_default ENABLE_GROUNDING 1
set_default ENABLE_YOUTUBE_CHANNEL_BACKFILL_AFTER_INGEST 1
set_default ENABLE_UPLOADER_BACKFILL 1
set_default DISCORD_CREATE_THREADS 1
set_default AUTONOMOUS_REFINE_ITERS 2
# export DISCORD_KB_CHANNEL_ID=123456789012345678
ENV
)

EOS
