"""Timeline manager utilities for the scoped Discord bot."""

from __future__ import annotations

from datetime import datetime as _dt
from datetime import timedelta
from platform.time import default_utc_now
from typing import Any


class TimelineManager:
    """Manages subject timelines and evidence consolidation."""

    def __init__(self) -> None:
        self.timelines: dict[str, list[dict]] = {}
        self.evidence_channels: dict[str, str] = {}

    def add_timeline_event(self, subject: str, event: dict[str, Any]) -> None:
        if subject not in self.timelines:
            self.timelines[subject] = []
        event_entry = {
            "timestamp": default_utc_now().isoformat(),
            "type": event.get("type", "general"),
            "title": event.get("title", ""),
            "description": event.get("description", ""),
            "source_url": event.get("source_url"),
            "confidence": event.get("confidence", 0.5),
            "evidence_refs": event.get("evidence_refs", []),
            "analytical_framing": event.get("analytical_framing", ""),
        }
        self.timelines[subject].append(event_entry)
        self.timelines[subject].sort(key=lambda x: x["timestamp"])

    def get_timeline_summary(self, subject: str, days: int = 30) -> str:
        if subject not in self.timelines:
            return f"No timeline data available for {subject}"
        cutoff = default_utc_now() - timedelta(days=days)
        recent_events = [e for e in self.timelines[subject] if _dt.fromisoformat(e["timestamp"]) > cutoff]
        if not recent_events:
            return f"No recent events for {subject} in the last {days} days"
        summary_lines = [f"**{subject} Timeline (Last {days} days)**\n"]
        for event in recent_events[-10:]:
            date = _dt.fromisoformat(event["timestamp"]).strftime("%m/%d")
            event_type = event["type"].title()
            title = event["title"][:50] + "..." if len(event["title"]) > 50 else event["title"]
            framing = f" • {event['analytical_framing'][:100]}..."
            summary_lines.append(f"• **{date}** [{event_type}] {title}{framing}")
        return "\n".join(summary_lines)


__all__ = ["TimelineManager"]
