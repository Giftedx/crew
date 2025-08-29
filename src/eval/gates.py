from __future__ import annotations

"""Regression gate helpers for evaluation reports."""


def compare(
    report: dict[str, dict[str, float]], baseline: dict[str, dict[str, float]]
) -> dict[str, object]:
    reasons: list[str] = []
    for task, base_metrics in baseline.items():
        current = report.get(task, {})
        if current.get("quality", 0.0) < base_metrics.get("quality", 0.0):
            reasons.append(
                f"{task} quality {current.get('quality', 0):.2f} < {base_metrics['quality']:.2f}"
            )
        if current.get("cost_usd", 0.0) > base_metrics.get("cost_usd", 0.0):
            reasons.append(
                f"{task} cost {current.get('cost_usd', 0):.2f} > {base_metrics['cost_usd']:.2f}"
            )
        if current.get("latency_ms", 0.0) > base_metrics.get("latency_ms", 0.0):
            reasons.append(
                f"{task} latency {current.get('latency_ms', 0):.1f} > {base_metrics['latency_ms']:.1f}"
            )
    return {"pass": not reasons, "reasons": reasons}


__all__ = ["compare"]
