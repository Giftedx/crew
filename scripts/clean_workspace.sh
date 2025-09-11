#!/usr/bin/env bash
set -euo pipefail

echo "[clean] Removing Python cache & bytecode"
find . -type d -name '__pycache__' -prune -exec rm -rf {} + 2>/dev/null || true
find . -type f -name '*.py[co]' -delete 2>/dev/null || true

echo "[clean] Removing test & coverage artifacts"
rm -rf .pytest_cache .mypy_cache .ruff_cache htmlcov coverage/ ruff_results || true
find . -maxdepth 1 -type f -name '.coverage*' -delete || true

echo "[clean] Removing build artifacts"
rm -rf build dist *.egg-info || true

echo "[clean] Removing temp files"
find . -type f \( -name '*~' -o -name '*.orig' -o -name '*.rej' -o -name '*.tmp' -o -name '*.bak' \) -delete || true

echo "[clean] Done. For deeper cleanup (envs, node_modules) run: make deep-clean"
