"""Persist and retrieve chronological events with references."""
from __future__ import annotations
import json
from typing import TYPE_CHECKING, Any, ClassVar, TypedDict, cast
from platform.observability.metrics import get_metrics
from platform.core.step_result import StepResult
from .. import settings
from ._base import BaseTool
if TYPE_CHECKING:
    from pathlib import Path

class _TimelineAddResult(TypedDict, total=False):
    status: str
    error: str

class _TimelineGetResult(TypedDict):
    status: str
    events: list[dict[str, object]]

class TimelineEvent(TypedDict, total=False):
    ts: int | float
    type: str
    data: dict[str, Any]
    clip: str
    context_verdict: str
    fact_verdict: str
    evidence: list[Any]

class TimelineTool(BaseTool[StepResult]):
    """Store timeline events per video with sources."""
    name: str = 'Timeline Tool'
    description: str = 'Record and fetch timeline events for videos.'
    model_config: ClassVar[dict[str, Any]] = {'extra': 'allow'}

    def __init__(self, storage_path: Path | None=None):
        super().__init__()
        self.storage_path = storage_path or settings.BASE_DIR / 'timeline.json'
        if not self.storage_path.exists():
            self._save({})
        self._metrics = get_metrics()

    def _load(self) -> dict[str, list[TimelineEvent]]:
        try:
            with self.storage_path.open('r', encoding='utf-8') as f:
                raw: Any = json.load(f)
        except Exception:
            return {}
        if not isinstance(raw, dict):
            return {}
        out: dict[str, list[TimelineEvent]] = {}
        for vid, events in raw.items():
            if not isinstance(vid, str) or not isinstance(events, list):
                continue
            norm_events: list[TimelineEvent] = []
            for ev in events:
                if not isinstance(ev, dict):
                    continue
                ts_val = ev.get('ts')
                ts: int | float | None = ts_val if isinstance(ts_val, int | float) else None
                type_val = ev.get('type')
                type_str = type_val if isinstance(type_val, str) else ''
                data_val = ev.get('data')
                data_dict = data_val if isinstance(data_val, dict) else {}
                norm: TimelineEvent = {'type': type_str, 'data': data_dict}
                if ts is not None:
                    norm['ts'] = ts
                if 'clip' in ev:
                    norm['clip'] = cast('Any', ev['clip'])
                if 'context_verdict' in ev:
                    norm['context_verdict'] = cast('Any', ev['context_verdict'])
                if 'fact_verdict' in ev:
                    norm['fact_verdict'] = cast('Any', ev['fact_verdict'])
                if 'evidence' in ev:
                    norm['evidence'] = cast('Any', ev['evidence'])
                norm_events.append(norm)
            out[vid] = norm_events
        return out

    def _save(self, data: dict[str, list[TimelineEvent]]) -> None:
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        with self.storage_path.open('w', encoding='utf-8') as f:
            json.dump(data, f)

    def add_event(self, video_id: str, event: TimelineEvent) -> None:
        data = self._load()
        events = data.get(video_id, [])
        events.append(event)
        events.sort(key=lambda x: x.get('ts') or 0)
        data[video_id] = events
        self._save(data)

    def get_timeline(self, video_id: str) -> list[TimelineEvent]:
        data = self._load()
        return data.get(video_id, [])

    def _run(self, action: str, **kwargs: object) -> StepResult:
        try:
            if action in {'add', 'record'}:
                video_id = cast('str', kwargs['video_id'])
                event = cast('TimelineEvent', kwargs.get('event', {}))
                self.add_event(video_id, event)
                self._metrics.counter('tool_runs_total', labels={'tool': 'timeline', 'outcome': 'success'}).inc()
                return StepResult.ok()
            if action == 'get':
                video_id = cast('str', kwargs['video_id'])
                events = self.get_timeline(video_id)
                self._metrics.counter('tool_runs_total', labels={'tool': 'timeline', 'outcome': 'success'}).inc()
                return StepResult.ok(events=events)
            self._metrics.counter('tool_runs_total', labels={'tool': 'timeline', 'outcome': 'skipped'}).inc()
            return StepResult.skip(reason='unknown action', action=action)
        except Exception as exc:
            self._metrics.counter('tool_runs_total', labels={'tool': 'timeline', 'outcome': 'error'}).inc()
            return StepResult.fail(error=str(exc))

    def run(self, action: str, **kwargs: object) -> StepResult:
        return self._run(action, **kwargs)