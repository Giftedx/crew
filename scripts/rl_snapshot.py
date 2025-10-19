"""CLI utility to dump or restore LearningEngine policy snapshots.

Usage:
  python -m scripts.rl_snapshot dump --out snapshot.json
  python -m scripts.rl_snapshot restore --in snapshot.json

The module discovers / constructs the global LearningEngine instance via a
lightweight factory (without pulling heavy optional dependencies). Adjust the
`build_engine()` function if your application wires a custom registry/policies.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from ultimate_discord_intelligence_bot.core.learning_engine import LearningEngine
from ultimate_discord_intelligence_bot.core.rl.policies.bandit_base import EpsilonGreedyBandit, ThompsonSamplingBandit, UCB1Bandit
from ultimate_discord_intelligence_bot.core.rl.policies.linucb import LinUCBDiagBandit
from ultimate_discord_intelligence_bot.core.rl.registry import PolicyRegistry

# Minimal domain seed list for snapshotting; adjust to match production usage.
DEFAULT_DOMAINS = {
    "route": EpsilonGreedyBandit(),
    "analysis": UCB1Bandit(),
    "retrieval": ThompsonSamplingBandit(),
    "linucb": LinUCBDiagBandit(),
}


def build_engine() -> LearningEngine:
    registry = PolicyRegistry()
    eng = LearningEngine(registry)
    # Register defaults if not already present
    for name, policy in DEFAULT_DOMAINS.items():
        if name not in registry:
            eng.register_domain(name, policy=policy)
    return eng


def cmd_dump(args: argparse.Namespace) -> int:
    eng = build_engine()
    snap = eng.snapshot()
    out_path = Path(args.out)
    out_path.write_text(json.dumps(snap, indent=2, sort_keys=True), encoding="utf-8")
    print(f"Snapshot written to {out_path}")
    return 0


def cmd_restore(args: argparse.Namespace) -> int:
    in_path = Path(args.input)
    if not in_path.exists():
        print(f"Snapshot file not found: {in_path}", file=sys.stderr)
        return 1
    data: Any = json.loads(in_path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        print("Invalid snapshot structure (expected JSON object)", file=sys.stderr)
        return 2
    eng = build_engine()
    skipped: list[str] = []
    # Pre-scan for future versions to report
    for domain, state in data.items():
        if isinstance(state, dict) and isinstance(state.get("version"), int) and state["version"] > 1:
            skipped.append(domain)
    eng.restore(data)
    # Optionally emit status summary
    status = eng.status()
    print(json.dumps(status, indent=2, sort_keys=True))
    if skipped:
        print(
            f"Skipped {len(skipped)} domain(s) with future version >1: {', '.join(skipped)}",
            file=sys.stderr,
        )
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="rl_snapshot", description="RL policy snapshot utility")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_dump = sub.add_parser("dump", help="Write snapshot JSON to --out path")
    p_dump.add_argument("--out", required=True, help="Output JSON path")
    p_dump.set_defaults(func=cmd_dump)

    p_restore = sub.add_parser("restore", help="Restore snapshot from --in / --input path")
    p_restore.add_argument("--in", "--input", dest="input", required=True, help="Input snapshot JSON path")
    p_restore.set_defaults(func=cmd_restore)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":  # pragma: no cover - manual invocation
    raise SystemExit(main())
