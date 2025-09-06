#!/usr/bin/env python3
"""Offline evaluation for reranker providers.

Input JSON format (list of records):
[
  {"query": "...", "docs": ["...", "..."], "label_index": 0},
  ...
]

Usage:
  python scripts/eval_reranker.py --provider cohere --file datasets/rerank_eval.json --topn 1
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from analysis.rerank import rerank


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--provider", required=True, help="cohere|jina")
    ap.add_argument("--file", required=True, help="path to JSON dataset")
    ap.add_argument("--topn", type=int, default=1)
    args = ap.parse_args()

    data = json.loads(Path(args.file).read_text(encoding="utf-8"))
    total = 0
    correct = 0
    for row in data:
        q = row["query"]
        docs = row["docs"]
        label = int(row.get("label_index", -1))
        rr = rerank(q, docs, provider=args.provider, top_n=max(1, min(args.topn, len(docs))))
        pred_top = rr.indexes[0] if rr.indexes else -1
        total += 1
        if pred_top == label:
            correct += 1
    acc = correct / max(1, total)
    print(json.dumps({"provider": args.provider, "items": total, "top1_acc": acc}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

