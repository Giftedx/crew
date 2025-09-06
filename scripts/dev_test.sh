#!/usr/bin/env bash
set -euo pipefail

# Developer helper script to run the test suite deterministically.
# Ensures we always invoke pytest via the project virtualenv interpreter
# to avoid PATH / shim ambiguity that caused earlier ModuleNotFoundError issues.
#
# Usage examples:
#   ./scripts/dev_test.sh                 # lightweight mode (fast collection)
#   FULL_STACK_TEST=1 ./scripts/dev_test.sh  # include heavy imports (FastAPI, discord, etc.)
#   TEST_PATTERN='test_discord_archiver.py::test_rest_api' ./scripts/dev_test.sh  # narrow selection
#
# Optional env vars:
#   TEST_PATTERN  - pytest node id or expression to run a subset
#   PYTEST_ADDOPTS - any extra flags (e.g. -k 'retry and not metrics')
#   FULL_STACK_TEST=1 - disable lightweight import guard

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_PY="${PROJECT_ROOT}/.venv/bin/python"

if [[ ! -x "${VENV_PY}" ]]; then
  echo "[dev_test] Could not find venv interpreter at ${VENV_PY}. Create a venv first (e.g. python -m venv .venv && . .venv/bin/activate && pip install -e .[dev])." >&2
  exit 1
fi

cd "${PROJECT_ROOT}"

PTN=${TEST_PATTERN:-}

echo "[dev_test] FULL_STACK_TEST=${FULL_STACK_TEST:-0} (export FULL_STACK_TEST=1 for heavy path)" >&2
echo "[dev_test] Using interpreter: ${VENV_PY}" >&2

if [[ -n "${PTN}" ]]; then
  echo "[dev_test] Running subset: ${PTN}" >&2
  exec "${VENV_PY}" -m pytest -q "${PTN}"
else
  echo "[dev_test] Running full suite" >&2
  exec "${VENV_PY}" -m pytest -q
fi
