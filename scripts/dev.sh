#!/usr/bin/env bash
set -euo pipefail

action="${1:-help}"

case "$action" in
  install)
    pip install -e .[dev]
    ;;
  lint)
    ruff check .
    ;;
  format)
    ruff check --fix . && ruff format .
    ;;
  type)
    # Full type check (non-fatal locally)
    mypy src || true
    ;;
  type-changed)
    # Type check only changed Python files relative to origin/main
    changed=$(git diff --name-only origin/main... | grep '\.py$' || true)
    if [ -z "$changed" ]; then
      echo "No changed Python files."; exit 0;
    fi
    echo "$changed" | tr '\n' '\0' | xargs -0 mypy || true
    ;;
  type-baseline)
    python scripts/type_baseline.py check || true
    ;;
  type-baseline-update)
    python scripts/type_baseline.py update || true
    ;;
  test)
    pytest -q
    ;;
  eval)
    python -m eval.runner datasets/golden/core/v1 baselines/golden/core/v1/summary.json || true
    ;;
  hooks)
    pre-commit install --install-hooks
    ;;
  *)
    echo "Usage: $0 {install|lint|format|type|type-changed|type-baseline|type-baseline-update|test|eval|hooks}" >&2
    exit 1
    ;;
 esac
