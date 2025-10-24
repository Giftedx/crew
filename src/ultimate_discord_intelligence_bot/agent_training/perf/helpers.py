from __future__ import annotations

from collections import Counter, defaultdict
from datetime import datetime, timedelta
from typing import Any

from core.time import default_utc_now  # type: ignore[import-not-found]

from .models import PerformanceMetric, ToolUsagePattern


def recent_interactions(history: dict[str, list[dict[str, Any]]], agent_name: str, days: int) -> list[dict[str, Any]]:
    cutoff_date = default_utc_now() - timedelta(days=days)
    return [
        interaction
        for interaction in history.get(agent_name, [])
        if ensure_utc(datetime.fromisoformat(interaction["timestamp"])) > cutoff_date
    ]


def calculate_trend(interactions: list[dict[str, Any]], metric_name: str, invert: bool = False) -> str:
    if len(interactions) < 10:
        return "insufficient_data"
    mid_point = len(interactions) // 2
    first_half = interactions[:mid_point]
    second_half = interactions[mid_point:]
    metric_extractors: dict[str, Any] = {
        "response_quality": lambda i: i.get("response_quality", 0.0),
        "response_time": lambda i: i.get("response_time", 0.0),
        "error_rate": lambda i: 1.0 if i.get("error_occurred", False) else 0.0,
        "user_satisfaction": lambda i: i.get("user_feedback", {}).get("satisfaction", 0.0),
        "tool_efficiency": lambda i: len(i.get("tools_used", [])) / max(1, len(i.get("tool_sequence", []))),
    }
    extractor = metric_extractors.get(metric_name, lambda i: 0.0)
    first_avg = sum(extractor(i) for i in first_half) / len(first_half)
    second_avg = sum(extractor(i) for i in second_half) / len(second_half)
    diff = second_avg - first_avg
    if invert:
        diff = -diff
    if abs(diff) < 0.05:
        return "stable"
    return "improving" if diff > 0 else "declining"


def calculate_tool_efficiency(interactions: list[dict[str, Any]]) -> float:
    if not interactions:
        return 0.0
    efficiency_scores = []
    for interaction in interactions:
        tools_used = interaction.get("tools_used", [])
        tool_sequence = interaction.get("tool_sequence", [])
        quality = interaction.get("response_quality", 0.0)
        if not tools_used:
            efficiency_scores.append(0.0)
            continue
        base_efficiency = quality / len(tools_used) if tools_used else 0.0
        sequence_bonus = 0.0
        if tool_sequence and len(tool_sequence) > 1:
            sequence_bonus = -0.1 if len(tool_sequence) > len(tools_used) * 1.5 else 0.1
        efficiency_scores.append(min(1.0, base_efficiency + sequence_bonus))
    return sum(efficiency_scores) / len(efficiency_scores)


def analyze_tool_usage(interactions: list[dict[str, Any]]) -> list[ToolUsagePattern]:
    tool_stats: dict[str, dict[str, Any]] = defaultdict(
        lambda: {
            "usage_count": 0,
            "success_count": 0,
            "quality_scores": [],
            "sequences": [],
            "errors": [],
        }
    )
    for interaction in interactions:
        tools_used = interaction.get("tools_used", [])
        quality = interaction.get("response_quality", 0.0)
        sequence = [step.get("tool", "") for step in interaction.get("tool_sequence", [])]
        for tool in tools_used:
            stats = tool_stats[tool]
            stats["usage_count"] += 1
            if quality > 0.7 and not interaction.get("error_occurred", False):
                stats["success_count"] += 1
            stats["quality_scores"].append(quality)
            if sequence:
                stats["sequences"].append(" -> ".join(sequence))
            if interaction.get("error_occurred", False):
                error_details = interaction.get("error_details", {})
                if tool in str(error_details):
                    stats["errors"].append(error_details.get("message", "Unknown error"))
    patterns = []
    for tool_name, stats in tool_stats.items():
        if stats["usage_count"]:
            success_rate = stats["success_count"] / stats["usage_count"]
            avg_quality = (
                sum(stats["quality_scores"]) / len(stats["quality_scores"]) if stats["quality_scores"] else 0.0
            )
            sequence_counter = Counter(stats["sequences"])
            common_sequences = [seq for seq, _ in sequence_counter.most_common(3)]
            patterns.append(
                ToolUsagePattern(
                    tool_name=tool_name,
                    usage_frequency=stats["usage_count"],
                    success_rate=success_rate,
                    average_quality_score=avg_quality,
                    common_sequences=common_sequences,
                    error_patterns=list(set(stats["errors"])),
                )
            )
    return sorted(patterns, key=lambda p: p.usage_frequency, reverse=True)


def calculate_performance_metrics_for_interactions(
    interactions: list[dict[str, Any]], thresholds: dict[str, float]
) -> list[PerformanceMetric]:
    if not interactions:
        return []
    quality_scores = [i.get("response_quality", 0.0) for i in interactions]
    avg_quality = sum(quality_scores) / len(quality_scores)
    metrics: list[PerformanceMetric] = []
    metrics.append(
        PerformanceMetric(
            metric_name="accuracy_target",
            target_value=thresholds.get("accuracy_target", 0.9),
            actual_value=avg_quality,
            trend="stable",  # placeholder; caller will override with real trend
            confidence=0.9 if len(quality_scores) > 10 else 0.7,
            last_updated=default_utc_now().isoformat(),
        )
    )
    response_times = [i.get("response_time", 0.0) for i in interactions]
    avg_response_time = sum(response_times) / len(response_times)
    metrics.append(
        PerformanceMetric(
            metric_name="response_time",
            target_value=thresholds.get("response_time", 30.0),
            actual_value=avg_response_time,
            trend="stable",  # placeholder; caller will override
            confidence=0.9,
            last_updated=default_utc_now().isoformat(),
        )
    )
    return metrics


__all__ = [
    "analyze_tool_usage",
    "calculate_performance_metrics_for_interactions",
    "calculate_tool_efficiency",
    "calculate_trend",
    "recent_interactions",
]
