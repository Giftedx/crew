"""Resolve YouTube channel handles to canonical channel URLs.

Contract: public run/_run returns StepResult; helper returns domain object.
"""

from __future__ import annotations

from dataclasses import dataclass
from platform.core.step_result import StepResult
from platform.observability.metrics import get_metrics

from ...profiles.schema import CanonicalChannel
from .._base import BaseTool


@dataclass
class YouTubeResolverTool(BaseTool[StepResult]):
    """Simple resolver mapping YouTube handles to canonical URLs."""

    name: str = "YouTube Resolver"
    description: str = "Resolve a YouTube handle to a canonical channel reference."

    def __post_init__(self) -> None:
        self._metrics = get_metrics()

    def _run(self, handle: str) -> StepResult:
        try:
            canonical = resolve_youtube_handle(handle)
            data = canonical.to_dict()
            self._metrics.counter("tool_runs_total", labels={"tool": "resolver_youtube", "outcome": "success"}).inc()
            return StepResult.ok(data=data)
        except Exception as exc:
            self._metrics.counter("tool_runs_total", labels={"tool": "resolver_youtube", "outcome": "error"}).inc()
            return StepResult.fail(error=str(exc))

    def run(self, handle: str) -> StepResult:
        return self._run(handle)


def resolve_youtube_handle(handle: str) -> CanonicalChannel:
    """Return a canonical reference for a YouTube handle.

    This performs enhanced normalization and validation. Real deployments
    should integrate with YouTube Data API for channel ID resolution.
    """
    handle = handle.strip()
    if "youtube.com/" in handle:
        if "/channel/" in handle:
            channel_id = handle.split("/channel/")[-1].split("?")[0]
            return CanonicalChannel(
                id=channel_id, handle=f"@{channel_id}", url=f"https://www.youtube.com/channel/{channel_id}"
            )
        elif "/@" in handle:
            norm = handle.split("/@")[-1].split("?")[0]
        elif "/c/" in handle:
            norm = handle.split("/c/")[-1].split("?")[0]
        else:
            norm = handle.split("/")[-1].split("?")[0]
    else:
        norm = handle.lstrip("@").strip()
    norm = norm.replace(" ", "").strip("/")
    channel_id = norm.lower()
    handle_url = f"https://www.youtube.com/@{norm}"
    return CanonicalChannel(id=channel_id, handle=f"@{norm}", url=handle_url)
