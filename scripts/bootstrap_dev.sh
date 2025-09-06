#!/usr/bin/env bash
# Dev environment bootstrap script.
# Idempotently creates a virtual environment, installs/updates dependencies,
# and ensures key developer tooling is present & current.
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")"/.. && pwd)"
cd "$PROJECT_ROOT"

VENV_DIR="${PROJECT_ROOT}/.venv"
# Detect python binary robustly
if command -v python >/dev/null 2>&1; then
  PYTHON_BIN="python"
elif command -v python3 >/dev/null 2>&1; then
  PYTHON_BIN="python3"
else
  echo "[bootstrap][error] Neither python nor python3 found on PATH" >&2
  exit 1
fi

log() { printf "\033[1;34m[bootstrap]\033[0m %s\n" "$*"; }
warn() { printf "\033[1;33m[bootstrap][warn]\033[0m %s\n" "$*"; }
err() { printf "\033[1;31m[bootstrap][error]\033[0m %s\n" "$*"; }

if [ ! -d "$VENV_DIR" ]; then
  log "Creating virtualenv in .venv";
  "$PYTHON_BIN" -m venv "$VENV_DIR"
fi

# shellcheck disable=SC1091
source "$VENV_DIR/bin/activate"

python -m pip install --upgrade pip wheel setuptools >/dev/null

if [ -f requirements.lock ]; then
  log "Installing dependencies from requirements.lock"
  pip install -r requirements.lock >/dev/null
else
  warn "requirements.lock missing; installing project deps (this may resolve broad ranges)."
  pip install .[dev] >/dev/null || pip install . >/dev/null || true
fi

log "Upgrading core dev tools (ruff, jedi, jedi-language-server)"
pip install --upgrade "ruff" "jedi>=0.19.1" "jedi-language-server>=0.41.0" >/dev/null || warn "Tool upgrade encountered an issue"

log "Environment summary:";
python - <<'PYINFO'
import sys, platform
print(f"Python: {sys.executable} ({sys.version.split()[0]}) on {platform.platform()}")
PYINFO
ruff version || warn "Ruff not found"
python -c 'import jedi; print("jedi:", jedi.__version__)'
python - <<'JLS'
import importlib.util
print("jedi-language-server present:", importlib.util.find_spec("jedi_language_server") is not None)
JLS

log "Done. Activate with: source .venv/bin/activate"
