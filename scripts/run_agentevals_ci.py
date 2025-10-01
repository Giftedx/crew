from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from eval.trajectory_evaluator import AgentTrajectory, TrajectoryEvaluator, TrajectoryStep


def _load_dataset(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        raise FileNotFoundError(f"Dataset not found: {path}")
    with path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, list):
        raise ValueError("Dataset must be a list of trajectory objects")
    return payload


def _build_trajectory(entry: dict[str, Any]) -> AgentTrajectory:
    steps_payload = entry.get("steps", [])
    steps: list[TrajectoryStep] = []
    for raw in steps_payload:
        if not isinstance(raw, dict):
            continue
        step_kwargs = {
            "timestamp": float(raw.get("timestamp", 0.0)),
            "agent_role": str(raw.get("agent_role", "unknown")),
            "action_type": str(raw.get("action_type", "unknown")),
            "content": str(raw.get("content", "")),
            "tool_name": raw.get("tool_name"),
            "tool_args": raw.get("tool_args"),
            "success": bool(raw.get("success", True)),
            "error": raw.get("error"),
        }
        steps.append(TrajectoryStep(**step_kwargs))

    return AgentTrajectory(
        session_id=str(entry.get("session_id", "unknown")),
        user_input=str(entry.get("user_input", "")),
        steps=steps,
        final_output=str(entry.get("final_output", "")),
        total_duration=float(entry.get("total_duration", 0.0)),
        success=bool(entry.get("success", True)),
        tenant=entry.get("tenant"),
        workspace=entry.get("workspace"),
    )


def _summarize(rows: list[dict[str, Any]]) -> dict[str, Any]:
    total = len(rows)
    success_count = sum(1 for row in rows if row.get("success"))
    accuracy_scores = [row["accuracy_score"] for row in rows if isinstance(row.get("accuracy_score"), (int, float))]
    avg_accuracy = sum(accuracy_scores) / len(accuracy_scores) if accuracy_scores else None
    return {
        "generated_at": datetime.now(UTC).isoformat(),
        "total_evaluations": total,
        "successful_evaluations": success_count,
        "average_accuracy_score": avg_accuracy,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run AgentEvals-inspired trajectory evaluation suite")
    parser.add_argument(
        "dataset",
        nargs="?",
        default="tests/data/trajectories/regression.json",
        help="Path to trajectory dataset (JSON list)",
    )
    parser.add_argument(
        "--report",
        default="reports/agentevals_ci.json",
        help="Optional output report path",
    )
    args = parser.parse_args(argv)

    dataset_path = Path(args.dataset).resolve()
    report_path = Path(args.report).resolve()

    os.environ.setdefault("ENABLE_TRAJECTORY_EVALUATION", "1")
    os.environ.setdefault("ENABLE_AGENT_EVALS", "0")

    try:
        raw_entries = _load_dataset(dataset_path)
    except Exception as exc:  # pragma: no cover - handled during CLI execution
        print(f"[agentevals-ci] Failed to load dataset: {exc}", file=sys.stderr)
        return 1

    evaluator = TrajectoryEvaluator()
    evaluation_rows: list[dict[str, Any]] = []

    for entry in raw_entries:
        if not isinstance(entry, dict):
            continue
        trajectory = _build_trajectory(entry)
        result = evaluator.evaluate_trajectory_accuracy(trajectory)
        row = result.to_dict()  # type: ignore[assignment]
        row.setdefault("session_id", trajectory.session_id)
        row.setdefault("evaluator", row.get("evaluator", "LLMHeuristic"))
        row["success"] = bool(result.success)
        row["trajectory_id"] = trajectory.session_id
        evaluation_rows.append(row)

    summary = _summarize(evaluation_rows)
    payload = {
        "summary": summary,
        "evaluations": evaluation_rows,
        "dataset": str(dataset_path),
    }

    report_path.parent.mkdir(parents=True, exist_ok=True)
    with report_path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)

    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":  # pragma: no cover - CLI entrypoint
    raise SystemExit(main())
