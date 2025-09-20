#!/usr/bin/env python
"""Utility to switch the active local model (env + simple validation).

Usage:
  python scripts/model_switcher.py --list
  python scripts/model_switcher.py --set primary
  python scripts/model_switcher.py --set /mnt/f/models/llama3.1-8b-instruct-awq

It updates a small state file `.active_model` and prints export commands
that the caller can eval in the shell:
  eval "$(python scripts/model_switcher.py --set primary)"

This avoids editing the .env directly while experimenting.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

try:
    # Load variables from .env if present so users don't need to `source`.
    from dotenv import load_dotenv  # type: ignore

    # Load early so LOGICAL mapping sees values. Do not override explicit env.
    load_dotenv(dotenv_path=Path(".env"), override=False)
except Exception:
    # Non-fatal: continue without auto-loading .env
    pass

STATE_FILE = Path(".active_model")

# Mapping of logical names -> env var (HF repo or local path)
LOGICAL = {
    "primary": os.environ.get("PRIMARY_MODEL_LOCAL") or os.environ.get("PRIMARY_MODEL_ID"),
    "secondary": os.environ.get("SECONDARY_MODEL_LOCAL") or os.environ.get("SECONDARY_MODEL_ID"),
    "fallback": os.environ.get("FALLBACK_SMALL_MODEL_LOCAL") or os.environ.get("FALLBACK_SMALL_MODEL_ID"),
    "math": os.environ.get("MATH_MODEL_ID"),
    "code": os.environ.get("CODE_MODEL_ID"),
}


def detect_model_path(model_ref: str) -> str:
    """Return a path or repo id; if a directory exists treat as local."""
    p = Path(model_ref)
    if p.exists() and p.is_dir():
        return str(p.resolve())
    return model_ref  # assume HF repo id


def list_models():
    rows = []
    for k, v in LOGICAL.items():
        if not v:
            continue
        resolved = detect_model_path(v)
        rows.append((k, v, resolved))
    width = max(len(r[0]) for r in rows) if rows else 7
    print("Available logical models:")
    for name, raw, resolved in rows:
        mark = "*" if STATE_FILE.exists() and STATE_FILE.read_text().strip() == resolved else " "
        print(f" {mark} {name.ljust(width)} -> {raw} (resolved: {resolved})")


def set_model(target: str):
    # Accept logical key or direct path / repo id
    candidate = LOGICAL.get(target, target)
    if not candidate:
        print(f"Error: unknown logical model '{target}'", file=sys.stderr)
        sys.exit(2)
    resolved = detect_model_path(candidate)
    # Write state
    STATE_FILE.write_text(resolved)
    # Print shell exports for caller
    print(f"export VLLM_MODEL_ID='{resolved}'")
    print(f"export ACTIVE_MODEL='{resolved}'")


def show_active():
    if STATE_FILE.exists():
        print("Active model:", STATE_FILE.read_text().strip())
    else:
        print("No active model set")


def parse_args(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--list", action="store_true", help="List logical models")
    ap.add_argument("--active", action="store_true", help="Show currently active model")
    ap.add_argument("--set", metavar="MODEL", help="Set model by logical name or path/repo id")
    return ap.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    acted = False
    if args.list:
        list_models()
        acted = True
    if args.active:
        show_active()
        acted = True
    if args.set:
        set_model(args.set)
        acted = True
    if not acted:
        print("No action provided. Use --list, --active or --set.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
