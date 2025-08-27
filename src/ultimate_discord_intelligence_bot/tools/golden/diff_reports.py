"""Compare two evaluation outputs and summarise deltas."""
from __future__ import annotations
import argparse, json

def main(argv=None) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--a", required=True)
    p.add_argument("--b", required=True)
    args = p.parse_args(argv)
    a = json.load(open(args.a))
    b = json.load(open(args.b))
    dq = b["aggregates"]["quality"] - a["aggregates"]["quality"]
    dc = b["aggregates"]["cost_usd"] - a["aggregates"]["cost_usd"]
    dl = b["aggregates"]["latency_ms"] - a["aggregates"]["latency_ms"]
    print(f"Δquality={dq:.3f} Δcost={dc:.3f} Δlatency={dl:.1f}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
