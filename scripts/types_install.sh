#!/usr/bin/env bash
# NOTE: Ensure this file is executable: chmod +x scripts/types_install.sh
set -euo pipefail

echo "[types_install] Ensuring virtual environment (optional)..."
if [[ -d .venv && -x .venv/bin/python ]]; then
  PYTHON=.venv/bin/python
else
  PYTHON=python
fi

echo "[types_install] Installing/upgrading baseline stub packages..."
${PYTHON} -m pip install --upgrade --quiet \
  types-psutil \
  types-jsonschema || true

echo "[types_install] Auto-installing any first-party stub suggestions (non-interactive)..."
${PYTHON} -m mypy --install-types --non-interactive || true

echo "[types_install] Done. Consider pinning new stub dependencies in pyproject optional dev extras."
