"""Discord-facing commands for debate analysis."""

from __future__ import annotations

from pathlib import Path
from platform.cache.tool_cache_decorator import cache_tool_result
from typing import TYPE_CHECKING, Any, ClassVar, TypedDict

from ultimate_discord_intelligence_bot.obs.metrics import get_metrics
from ultimate_discord_intelligence_bot.step_result import StepResult

from ..debate_analysis_pipeline import DebateAnalysisPipeline
from ..profiles.schema import CreatorProfile, Platforms, load_seeds
from ..profiles.store import ProfileStore
from ..tools.platform_resolver import (
    resolve_podcast_query,
    resolve_social_handle,
    resolve_twitch_login,
    resolve_youtube_handle,
)
from ._base import BaseTool


if TYPE_CHECKING:
    from collections.abc import Callable


class _DebateCommandResult(TypedDict, total=False):
    status: str
    error: str
    context: Any
    results: Any
    events: Any
    profile: Any
    collabs: Any
    compare: Any
    verified: list[str]
    trends: Any


class DebateCommandTool(BaseTool[StepResult]):
    """Expose debate analysis features through simple commands."""

    name: str = "Debate Command Tool"
    description: str = "Run debate analysis, context lookup and leaderboard ops."
    model_config: ClassVar[dict[str, Any]] = {"extra": "allow"}

    def __init__(
        self,
        pipeline: DebateAnalysisPipeline | None = None,
        ethan_defender: Callable[[str], str] | None = None,
        hasan_defender: Callable[[str], str] | None = None,
        profile_store: ProfileStore | None = None,
    ) -> None:
        super().__init__()
        if pipeline is None:
            pipeline = DebateAnalysisPipeline(ethan_defender=ethan_defender, hasan_defender=hasan_defender)
        self.pipeline = pipeline
        self.index = self.pipeline.index_tool
        self.fact_checker = self.pipeline.fact_checker
        self.leaderboard = self.pipeline.leaderboard
        self.timeline = self.pipeline.timeline
        self.trust_tracker = self.pipeline.trust_tracker
        self.profile_tool = self.pipeline.profile_tool
        self.profile_store = profile_store or ProfileStore(":memory:")
        self._metrics = get_metrics()

    @cache_tool_result(namespace="tool:debate_command", ttl=1800)
    def _run(self, command: str, **kwargs: Any) -> StepResult:
        """Dispatch debate related commands via a simple registry to reduce branches.

        Always returns a structured _DebateCommandResult. Underlying helpers that
        produce arbitrary dict payloads (e.g. analyze / claim) are wrapped so the
        top-level contract is consistent for callers & typing.
        """

        def analyze() -> _DebateCommandResult:
            analysis = self.pipeline.analyze(
                kwargs["url"],
                kwargs.get("ts", 0.0),
                kwargs.get("clip_text", ""),
                kwargs.get("person", "unknown"),
                transcript=kwargs.get("transcript"),
            )
            if isinstance(analysis, dict) and "status" not in analysis:
                analysis["status"] = "success"
            return analysis

        def context() -> StepResult:
            ctx = self.index.get_context(kwargs["video_id"], kwargs.get("ts", 0.0))
            return StepResult.ok(data={"context": ctx})

        def claim() -> StepResult:
            res = self.fact_checker.run(kwargs["claim"])
            raw = res if isinstance(res, StepResult) else StepResult.from_dict(res)
            if not raw.success:
                return StepResult.fail(error=raw.error or "fact checker failed")
            result: dict[str, Any] = dict(raw.data or {})
            person = kwargs.get("person")
            if person:
                verdict = result.get("verdict")
                lies = 1 if verdict == "false" else 0
                misinfo = 1 if result.get("evidence") else 0
                self.leaderboard.update_scores(person, lies, 0, misinfo)
                self.trust_tracker.run(person, verdict != "false")
                self.profile_tool.record_event(
                    person,
                    {
                        "video_id": "claim",
                        "ts": 0,
                        "clip": kwargs["claim"],
                        "fact_verdict": verdict,
                        "context_verdict": "n/a",
                        "evidence": result.get("evidence", []),
                    },
                )
            return StepResult.ok(data=result)

        def leaderboard() -> StepResult:
            return StepResult.ok(data={"results": self.leaderboard.get_top(kwargs.get("n", 10))})

        def timeline() -> StepResult:
            return StepResult.ok(data={"events": self.timeline.get_timeline(kwargs["video_id"])})

        def profile() -> StepResult:
            return StepResult.ok(data={"profile": self.profile_tool.get_profile(kwargs["person"])})

        def latest() -> StepResult:
            prof = self.profile_tool.get_profile(kwargs["person"])
            raw_events = prof.get("events", [])

            def _key(e: dict[str, object]) -> float:
                ts = e.get("ts", 0)
                try:
                    return float(ts)
                except Exception:
                    return 0.0

            events = sorted([ev for ev in raw_events if isinstance(ev, dict)], key=_key, reverse=True)
            return StepResult.ok(data={"events": events[: kwargs.get("n", 5)]})

        def collabs() -> StepResult:
            return StepResult.ok(data={"collabs": self.profile_store.get_collaborators(kwargs["person"])})

        def trends() -> StepResult:
            return StepResult.ok(data={"trends": []})

        def compare() -> StepResult:
            a_key = kwargs["a"]
            b_key = kwargs["b"]
            return StepResult.ok(
                data={
                    "compare": {
                        a_key: self.profile_store.get_collaborators(a_key),
                        b_key: self.profile_store.get_collaborators(b_key),
                    }
                }
            )

        def verify_profiles() -> StepResult:
            seed_path = kwargs.get("seeds", "profiles.yaml")
            try:
                if seed_path == "profiles.yaml":
                    local = Path(seed_path)
                    if not local.exists():
                        candidate = Path(__file__).resolve().parents[3] / "config" / "profiles.yaml"
                        if candidate.exists():
                            seed_path = str(candidate)
                seeds = load_seeds(seed_path)
            except Exception as exc:
                return StepResult.fail(error=f"Failed loading seeds: {exc}")
            verified: list[str] = []
            for seed in seeds:
                handles = seed.seed_handles
                platforms = Platforms()
                if yt := handles.get("youtube"):
                    platforms.youtube = [resolve_youtube_handle(yt[0])]
                if tw := handles.get("twitch"):
                    platforms.twitch = [resolve_twitch_login(tw[0])]
                if pod := handles.get("podcast"):
                    platforms.podcast = [resolve_podcast_query(pod[0])]
                for social in ("twitter", "instagram", "tiktok"):
                    if social in handles:
                        getattr(platforms, social).append(resolve_social_handle(social, handles[social][0]))
                profile_obj = CreatorProfile(
                    name=seed.name,
                    type=seed.type,
                    roles=seed.roles,
                    shows=seed.shows,
                    content_tags=seed.content_tags,
                    platforms=platforms,
                )
                self.profile_store.upsert_profile(profile_obj)
                verified.append(seed.name)
            return StepResult.ok(data={"verified": verified})

        registry: dict[str, Callable[[], Any]] = {
            "analyze": analyze,
            "context": context,
            "claim": claim,
            "leaderboard": leaderboard,
            "timeline": timeline,
            "profile": profile,
            "creator": profile,
            "latest": latest,
            "collabs": collabs,
            "trends": trends,
            "compare": compare,
            "verify_profiles": verify_profiles,
        }
        handler = registry.get(command)
        if handler is None:
            self._metrics.counter("tool_runs_total", labels={"tool": "debate_command", "outcome": "skipped"}).inc()
            return StepResult.skip(reason="unknown command", data={"command": command})
        try:
            result = handler()
        except Exception as exc:
            self._metrics.counter("tool_runs_total", labels={"tool": "debate_command", "outcome": "error"}).inc()
            return StepResult.fail(error=str(exc))
        if isinstance(result, StepResult):
            return result
        if not isinstance(result, dict):
            self._metrics.counter("tool_runs_total", labels={"tool": "debate_command", "outcome": "error"}).inc()
            return StepResult.fail(error="handler returned unexpected type")
        self._metrics.counter("tool_runs_total", labels={"tool": "debate_command", "outcome": "success"}).inc()
        return StepResult.ok(data=result)

    def run(self, *args: Any, **kwargs: Any) -> StepResult:
        command = str(args[0]) if args else str(kwargs.get("command", ""))
        try:
            return self._run(command, **kwargs)
        except Exception as exc:
            self._metrics.counter("tool_runs_total", labels={"tool": "debate_command", "outcome": "error"}).inc()
            return StepResult.fail(error=str(exc))
