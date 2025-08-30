"""Simple evaluation runner used in tests and CI."""

from __future__ import annotations

import argparse
import json
from collections.abc import Callable
from pathlib import Path
from typing import Any

from . import scorers
from .loader import load_cases

# Type alias for the model function used in tests.
ModelFunc = Callable[[str, dict[str, Any]], tuple[str, dict[str, float]]]


def run(
    dataset_dir: str | Path, model: ModelFunc, tenant: str | None = None
) -> dict[str, dict[str, float]]:
    """Run the evaluation suite.

    Parameters
    ----------
    dataset_dir:
        Directory containing task JSONL files.
    model:
        Callable taking ``(task, case)`` and returning ``(output, meta)``
        where ``meta`` can include ``cost_usd`` and ``latency_ms``.
    tenant:
        Optional tenant slug for dataset overrides.
    """

    root = Path(dataset_dir)
    cases = load_cases(root, tenant)
    report: dict[str, dict[str, float]] = {}
    for task, items in cases.items():
        quality = 0.0
        total_cost = 0.0
        total_latency = 0.0
        for case in items:
            output, meta = model(task, case)
            score = 0.0
            if task == "rag_qa":
                if scorers.must_include(output, case.get("must_include", [])) and scorers.forbidden(
                    output, case.get("forbidden", [])
                ):
                    score = 1.0
            elif task == "summarize":
                if scorers.must_include(output, case.get("expected_keywords", [])):
                    score = 1.0
            elif task == "classification":
                if scorers.classification(output, case.get("expected", "")):
                    score = 1.0
            elif task == "claimcheck":
                if scorers.claimcheck(output, case.get("expected_label", "")):
                    score = 1.0
            elif task == "tool_tasks":
                schema = {k: type(v) for k, v in case.get("expected", {}).items()}
                if scorers.json_schema(output, schema):
                    score = 1.0
            quality += score
            total_cost += float(meta.get("cost_usd", 0.0))
            total_latency += float(meta.get("latency_ms", 0.0))
        n = len(items) or 1
        report[task] = {
            "quality": quality / n,
            "cost_usd": total_cost,
            "latency_ms": total_latency / n,
        }
    return report


def main() -> None:

    p = argparse.ArgumentParser(description="run evaluation suite")
    p.add_argument("dataset", type=str, help="dataset directory")
    p.add_argument("baseline", type=str, nargs="?", help="path to baseline summary.json")
    p.add_argument(
        "--out", type=str, default="reports/eval/latest.json", help="where to write report"
    )
    args = p.parse_args()

    def echo_model(task: str, case: dict[str, Any]) -> tuple[str, dict[str, float]]:
        # trivial model that echoes expected answers for CI sanity checks
        if task == "rag_qa":
            return case.get("must_include", [""])[0], {"cost_usd": 0.0, "latency_ms": 0}
        if task == "summarize":
            return " ".join(case.get("expected_keywords", [])), {"cost_usd": 0.0, "latency_ms": 0}
        if task == "classification":
            return case.get("expected", ""), {"cost_usd": 0.0, "latency_ms": 0}
        if task == "claimcheck":
            return case.get("expected_label", ""), {"cost_usd": 0.0, "latency_ms": 0}
        if task == "tool_tasks":
            return json.dumps(case.get("expected", {})), {"cost_usd": 0.0, "latency_ms": 0}
        return "", {"cost_usd": 0.0, "latency_ms": 0}

    report = run(args.dataset, echo_model)
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    with open(args.out, "w") as f:
        json.dump(report, f, indent=2)

    if args.baseline:
        from .gates import compare  # noqa: PLC0415 - local import avoids heavy dependency on baseline-less runs

        with open(args.baseline) as f:
            base = json.load(f)
        result = compare(report, base)
        if not result["pass"]:
            reasons = result.get("reasons")
            if isinstance(reasons, list):
                for r in reasons:
                    print("FAIL:", r)
            else:  # defensive: unexpected shape
                print("FAIL:", reasons)
            raise SystemExit(1)


if __name__ == "__main__":
    main()
