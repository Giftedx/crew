"""Resolve Twitch logins to canonical channel URLs.

Contract: public run/_run returns StepResult; helpers return plain dicts/domain objects.
"""

from __future__ import annotations

from dataclasses import dataclass

from ultimate_discord_intelligence_bot.obs.metrics import get_metrics
from ultimate_discord_intelligence_bot.step_result import StepResult

from ...profiles.schema import CanonicalChannel
from .._base import BaseTool


@dataclass
class TwitchResolverTool(BaseTool[StepResult]):
    """Simple resolver mapping Twitch logins to canonical URLs."""

    name: str = "Twitch Resolver"
    description: str = "Resolve a Twitch login name to a canonical channel reference."

    def __post_init__(self) -> None:  # pragma: no cover - trivial init
        self._metrics = get_metrics()

    def _run(self, login: str) -> StepResult:  # pragma: no cover - mapping only
        try:
            canonical = resolve_twitch_login(login)
            data = canonical.to_dict()
            self._metrics.counter(
                "tool_runs_total",
                labels={"tool": "resolver_twitch", "outcome": "success"},
            ).inc()
            return StepResult.ok(data=data)
        except Exception as exc:
            self._metrics.counter(
                "tool_runs_total",
                labels={"tool": "resolver_twitch", "outcome": "error"},
            ).inc()
            return StepResult.fail(error=str(exc))

    def run(self, login: str) -> StepResult:  # thin explicit wrapper
        return self._run(login)


def resolve_twitch_login(login: str) -> CanonicalChannel:
    norm = login.replace("https://", "").replace("twitch.tv/", "").strip("/")
    channel_id = norm.lower()
    url = f"https://twitch.tv/{norm}"
    return CanonicalChannel(id=channel_id, handle=norm, url=url)
