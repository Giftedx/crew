"""Offline evaluation harness for golden datasets."""
from __future__ import annotations

import argparse
import json
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Callable, Dict, List, Any

import jsonschema
import yaml

from .memory_service import MemoryService  # reuse existing service if needed


@dataclass
class SampleResult:
    record: Dict[str, Any]
    output: str
    quality: float
    cost_usd: float
    latency_ms: float
    scores: Dict[str, float]


@dataclass
class EvalResult:
    samples: List[SampleResult]
    aggregates: Dict[str, float]


# --- Scorers ---------------------------------------------------------------

def score_must_include(output: str, expected: Dict[str, Any]) -> float:
    phrases = expected.get("must_include", [])
    if not phrases:
        return 1.0
    hits = sum(1 for p in phrases if p.lower() in output.lower())
    return hits / len(phrases)

def score_must_link(output: str, expected: Dict[str, Any]) -> float:
    links = expected.get("must_link", [])
    if not links:
        return 1.0
    hits = sum(1 for l in links if l in output)
    return hits / len(links)

def score_forbidden(output: str, expected: Dict[str, Any]) -> float:
    bad = expected.get("forbidden", [])
    return 1.0 if all(b.lower() not in output.lower() for b in bad) else 0.0

def score_coverage(output: str, expected: Dict[str, Any]) -> float:
    phrases = expected.get("must_include", [])
    if not phrases:
        return 1.0
    return score_must_include(output, expected)

def score_grounded(output: str, record: Dict[str, Any]) -> float:
    refs = record.get("input", {}).get("context_refs", [])
    if not refs:
        return 1.0
    hits = sum(1 for r in refs if r.get("id") and r["id"] in output)
    return hits / len(refs)

SCORERS = {
    "must_include": score_must_include,
    "must_link": score_must_link,
    "forbidden": score_forbidden,
    "coverage": score_coverage,
    "grounded": score_grounded,
}

# --- Evaluation ------------------------------------------------------------

def run_dataset(
    dataset_path: Path,
    runner: Callable[[Dict[str, Any]], Dict[str, Any]],
    seed: int = 0,
) -> EvalResult:
    schema = json.load(open("datasets/schemas/task_record.schema.json"))
    samples: List[SampleResult] = []
    for line in dataset_path.read_text().splitlines():
        record = json.loads(line)
        jsonschema.validate(record, schema)
        result = runner(record["input"])
        output = result.get("output", "")
        cost = float(result.get("cost_usd", 0))
        latency = float(result.get("latency_ms", 0))
        scores = {name: fn(output, record["expected"]) if name != "grounded" else fn(output, record)
                  for name, fn in SCORERS.items()}
        quality = sum(scores.values()) / len(scores)
        samples.append(
            SampleResult(record=record, output=output, quality=quality,
                         cost_usd=cost, latency_ms=latency, scores=scores)
        )
    # aggregates
    if samples:
        quality_avg = sum(s.quality for s in samples) / len(samples)
        cost_sum = sum(s.cost_usd for s in samples)
        latency_avg = sum(s.latency_ms for s in samples) / len(samples)
    else:
        quality_avg = cost_sum = latency_avg = 0.0
    aggregates = {
        "quality": quality_avg,
        "cost_usd": cost_sum,
        "latency_ms": latency_avg,
        "lambda": 0.0,
        "mu": 0.0,
    }
    return EvalResult(samples=samples, aggregates=aggregates)

# --- Baseline comparison ---------------------------------------------------

def compare_to_baseline(result: EvalResult, key: str, tolerances: Dict[str, float]) -> bool:
    baseline = yaml.safe_load(open("benchmarks/baselines.yaml"))
    if key not in baseline:
        return True
    base = baseline[key]
    return (
        result.aggregates["quality"] >= base["quality"] - tolerances.get("quality", 0.0)
        and result.aggregates["cost_usd"] <= base["cost_usd"] + tolerances.get("cost_usd", 0.0)
        and result.aggregates["latency_ms"] <= base["latency_ms"] + tolerances.get("latency_ms", 0.0)
    )

# --- CLI ------------------------------------------------------------------

def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="eval_harness")
    sub = parser.add_subparsers(dest="cmd", required=True)
    run_p = sub.add_parser("run")
    run_p.add_argument("--dataset", required=True)
    run_p.add_argument("--task", required=True)
    run_p.add_argument("--router-profile", required=False)
    run_p.add_argument("--seed", type=int, default=0)
    run_p.add_argument("--out", required=True)
    args = parser.parse_args(argv)

    def dummy_runner(_input: Dict[str, Any]) -> Dict[str, Any]:
        return {"output": "no", "cost_usd": 0.0, "latency_ms": 0.0}

    result = run_dataset(Path(args.dataset), dummy_runner, seed=args.seed)
    out_json = Path(args.out)
    out_json.parent.mkdir(parents=True, exist_ok=True)
    with open(out_json, "w") as f:
        json.dump(
            {
                "samples": [asdict(s) for s in result.samples],
                "aggregates": result.aggregates,
            },
            f,
            indent=2,
        )
    with open(out_json.with_suffix(".md"), "w") as f:
        f.write(f"Quality: {result.aggregates['quality']:.3f}\n")
        f.write(f"Cost USD: {result.aggregates['cost_usd']:.3f}\n")
        f.write(f"Latency ms: {result.aggregates['latency_ms']:.1f}\n")
    ok = compare_to_baseline(result, Path(args.dataset).stem + "_v1", {
        "quality": 0.5,
        "cost_usd": 0.0,
        "latency_ms": 50.0,
    })
    return 0 if ok else 1

if __name__ == "__main__":
    raise SystemExit(main())
