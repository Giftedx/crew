#!/usr/bin/env bash
set -euo pipefail

# Download and prepare selected models into /mnt/f/models with optional quantization notes.
# This script avoids re-downloading if a target directory already exists.
# Requires: huggingface_hub (via transformers), git-lfs (for some repos), and adequate disk space.

PARALLEL=${MODEL_DOWNLOAD_WORKERS:-4}
BASE_DIR="/mnt/f/models"
CACHE_DIR="${HF_HOME:-/mnt/f/hf_cache}"

mkdir -p "${BASE_DIR}" "${CACHE_DIR}" "${CACHE_DIR}/transformers" "${CACHE_DIR}/datasets"

# Resolve local directory basenames safely (tolerate unset env under `set -u`).
PRIMARY_LOCAL="${PRIMARY_MODEL_LOCAL:-/mnt/f/models/llama3.1-8b-instruct-awq}"
SECONDARY_LOCAL="${SECONDARY_MODEL_LOCAL:-/mnt/f/models/qwen2.5-7b-instruct-awq}"
FALLBACK_LOCAL="${FALLBACK_SMALL_MODEL_LOCAL:-/mnt/f/models/phi-3.5-mini}"
MATH_LOCAL="${MATH_MODEL_LOCAL:-/mnt/f/models/mathstral-7b}"
CODE_LOCAL="${CODE_MODEL_LOCAL:-/mnt/f/models/starcoder2-7b}"

PRIMARY_BASE="${PRIMARY_LOCAL##*/}"
SECONDARY_BASE="${SECONDARY_LOCAL##*/}"
FALLBACK_BASE="${FALLBACK_LOCAL##*/}"
MATH_BASE="${MATH_LOCAL##*/}"
CODE_BASE="${CODE_LOCAL##*/}"

# Model list (repo_id  local_dir  group_tag)
# Start with defaults
MODELS=( \
  "${PRIMARY_MODEL_ID:-meta-llama/Meta-Llama-3.1-8B-Instruct} ${PRIMARY_BASE} primary" \
  "${SECONDARY_MODEL_ID:-Qwen/Qwen2.5-7B-Instruct} ${SECONDARY_BASE} secondary" \
  "${FALLBACK_SMALL_MODEL_ID:-microsoft/Phi-3.5-mini-instruct} ${FALLBACK_BASE} fallback" \
  "${MATH_MODEL_ID:-mistralai/Mathstral-7B-v0.1} ${MATH_BASE} math" \
  "${CODE_MODEL_ID:-bigcode/starcoder2-7b} ${CODE_BASE} code" \
)

# Optional AWQ overrides if provided via env (e.g., PRIMARY_MODEL_AWQ_REPO="TheBloke/Llama-3.1-8B-Instruct-AWQ")
if [[ -n "${PRIMARY_MODEL_AWQ_REPO:-}" ]]; then
  MODELS+=( "${PRIMARY_MODEL_AWQ_REPO} ${PRIMARY_BASE} primary-awq" )
fi
if [[ -n "${SECONDARY_MODEL_AWQ_REPO:-}" ]]; then
  MODELS+=( "${SECONDARY_MODEL_AWQ_REPO} ${SECONDARY_BASE} secondary-awq" )
fi
if [[ -n "${MATH_MODEL_AWQ_REPO:-}" ]]; then
  MODELS+=( "${MATH_MODEL_AWQ_REPO} ${MATH_BASE}-awq math-awq" )
fi
if [[ -n "${CODE_MODEL_AWQ_REPO:-}" ]]; then
  MODELS+=( "${CODE_MODEL_AWQ_REPO} ${CODE_BASE}-awq code-awq" )
fi

usage() {
  echo "Usage: $0 [all|primary|secondary|fallback|math|code|primary-awq|secondary-awq|math-awq|code-awq|awq]" >&2
  exit 1
}

TARGET_GROUP=${1:-all}

filter_models() {
  local target=$1
  if [[ $target == "all" ]]; then
    printf '%s\n' "${MODELS[@]}"
    return
  fi
  # Special group: awq → any tag that ends with -awq
  if [[ $target == "awq" ]]; then
    for m in "${MODELS[@]}"; do
      set -- $m
      # shellcheck disable=SC2034
      local repo_id=$1; local local_dir=$2; local tag=$3
      if [[ "$tag" == *"-awq" ]]; then
        echo "$m"
      fi
    done
    return
  fi
  for m in "${MODELS[@]}"; do
    set -- $m
    # shellcheck disable=SC2034
    local repo_id=$1; local local_dir=$2; local tag=$3
    if [[ "$tag" == "$target" ]]; then
      echo "$m"
    fi
  done
}

mapfile -t SELECTED < <(filter_models "$TARGET_GROUP")
if [[ ${#SELECTED[@]} -eq 0 ]]; then
  echo "No models matched group '$TARGET_GROUP'" >&2
  usage
fi

# Download function (sequential within GNU parallel if available)
fetch_model() {
  local repo_id=$1
  local local_dir=$2
  local tag=$3
  local dest="${BASE_DIR}/${local_dir}"

  if [[ -d "${dest}" ]]; then
    echo "[SKIP] ${repo_id} already at ${dest}" >&2
    return 0
  fi
  echo "[FETCH] ${repo_id} -> ${dest}" >&2
  python - <<PYEOF
import os, sys
from huggingface_hub import snapshot_download
repo_id = "${repo_id}"
dest = "${dest}"
os.makedirs(dest, exist_ok=True)
# Selectively ignore large safetensors if quantized versions appear later (placeholder logic now)
try:
    snapshot_download(repo_id, local_dir=dest, resume_download=True, max_workers=8)
    print(f"Downloaded {repo_id} to {dest}")
except Exception as e:
    print(f"[WARN] Failed to download {repo_id}: {e}")
    # Do not fail the whole script for optional groups
    sys.exit(0)
PYEOF
}

export -f fetch_model
export BASE_DIR

# Prepare input lines for parallel execution
PARALLEL_INPUT=$(mktemp)
for line in "${SELECTED[@]}"; do
  echo "$line" >> "$PARALLEL_INPUT"
done

if command -v parallel >/dev/null 2>&1; then
  parallel -j "$PARALLEL" --colsep ' ' fetch_model :::: "$PARALLEL_INPUT"
else
  echo "GNU parallel not found; downloading sequentially." >&2
  while read -r repo local tag; do
    fetch_model "$repo" "$local" "$tag"
  done < "$PARALLEL_INPUT"
fi

rm -f "$PARALLEL_INPUT"

echo "All requested models processed."
