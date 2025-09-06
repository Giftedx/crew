#!/usr/bin/env bash
set -euo pipefail

# ensure_venv.sh: create or reuse local .venv and install project in editable dev mode if needed.
# Usage:
#   ./scripts/ensure_venv.sh            # create & install if missing
#   FORCE_REINSTALL=1 ./scripts/ensure_venv.sh   # reinstall deps
#   SKIP_INSTALL=1 ./scripts/ensure_venv.sh      # only create venv if absent
#   EXTRA='-e ".[dev,test]"' ./scripts/ensure_venv.sh  # custom extras (defaults to '.[dev]')
#
# Idempotent: safe to call multiple times.

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

PYTHON_BIN="${PYTHON_BIN:-python3}"
VENV_DIR="${VENV_DIR:-.venv}"
EXTRAS_SPEC="${EXTRAS_SPEC:-'.[dev]'}"

if [[ ! -d "$VENV_DIR" ]]; then
  echo "[ensure_venv] Creating virtual environment in $VENV_DIR"
  "$PYTHON_BIN" -m venv "$VENV_DIR"
fi

# shellcheck disable=SC1091
source "$VENV_DIR/bin/activate"

if [[ "${FORCE_REINSTALL:-0}" == "1" ]]; then
  echo "[ensure_venv] Forcing reinstall of editable package"
  pip uninstall -y ultimate_discord_intelligence_bot >/dev/null 2>&1 || true
fi

if [[ "${SKIP_INSTALL:-0}" == "1" ]]; then
  echo "[ensure_venv] SKIP_INSTALL=1 set; skipping dependency installation"
  exit 0
fi

# Determine whether install is needed
if python -c "import ultimate_discord_intelligence_bot" 2>/dev/null; then
  echo "[ensure_venv] Package already importable; ensuring extras up to date"
else
  echo "[ensure_venv] Installing project with extras: $EXTRAS_SPEC"
fi

# Quote extras to survive zsh/bash globbing
pip install -q -e "$EXTRAS_SPEC"

# Optional: install pre-commit hooks if present
if [[ -f .pre-commit-config.yaml ]]; then
  pre-commit install --install-hooks >/dev/null 2>&1 || true
fi

echo "[ensure_venv] Complete: $(python -V) @ $VIRTUAL_ENV"
