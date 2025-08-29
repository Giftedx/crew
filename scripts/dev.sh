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
    mypy src || true
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
    echo "Usage: $0 {install|lint|format|type|test|eval|hooks}" >&2
    exit 1
    ;;
 esac
