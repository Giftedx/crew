"""Generic social profile resolver for platforms like X, Instagram, TikTok.

Contract: public run/_run returns StepResult; helper returns domain object.
"""

from __future__ import annotations
from dataclasses import dataclass
from platform.observability.metrics import get_metrics
from platform.core.step_result import StepResult
from ...profiles.schema import CanonicalProfile
from .._base import BaseTool


@dataclass
class SocialResolverTool(BaseTool[StepResult]):
    """Resolve a social handle on a given platform to a canonical profile."""

    name: str = "Social Resolver"
    description: str = "Resolve social handles for platforms like X, Instagram, or TikTok."

    def __post_init__(self) -> None:
        self._metrics = get_metrics()

    def _run(self, platform: str, handle: str) -> StepResult:
        try:
            profile = resolve_social_handle(platform, handle)
            data = profile.to_dict()
            self._metrics.counter("tool_runs_total", labels={"tool": "resolver_social", "outcome": "success"}).inc()
            return StepResult.ok(data=data)
        except Exception as exc:
            self._metrics.counter("tool_runs_total", labels={"tool": "resolver_social", "outcome": "error"}).inc()
            return StepResult.fail(error=str(exc))

    def run(self, platform: str, handle: str) -> StepResult:
        return self._run(platform, handle)


def resolve_social_handle(platform: str, handle: str) -> CanonicalProfile:
    norm_handle = handle.lstrip("@").strip()
    url = f"https://{platform}.com/{norm_handle}" if platform else None
    return CanonicalProfile(id=norm_handle.lower(), handle=f"@{norm_handle}", url=url)
