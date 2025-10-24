#!/usr/bin/env python3
"""Wrapper script for running evaluations with proper Python path."""

import sys
from pathlib import Path


# Ensure src is on path before importing project modules.
repo_root = Path(__file__).parent.parent
src_path = repo_root / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from eval.runner import main  # noqa: E402  (path injected directly above)


def main_wrapper() -> None:  # thin wrapper for symmetry with other scripts
    main()


if __name__ == "__main__":  # pragma: no cover - simple script entrypoint
    main_wrapper()
