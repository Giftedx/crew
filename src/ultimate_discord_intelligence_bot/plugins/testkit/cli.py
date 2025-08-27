"""Command line interface for plugin capability tests."""
from __future__ import annotations

import argparse
import json
import sys

from .runner import run


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run plugin capability tests")
    parser.add_argument("--plugin", required=True, help="plugin import path")
    args = parser.parse_args(argv)

    report = run(args.plugin)
    print(json.dumps(report, indent=2))
    # non-zero exit if any scenario failed
    if any(not r["passed"] for r in report["results"]):
        return 1
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
