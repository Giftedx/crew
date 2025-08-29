"""Discord-facing commands for debate analysis."""

from __future__ import annotations

from collections.abc import Callable

from crewai.tools import BaseTool

from ..profiles.schema import (
    CreatorProfile,
    Platforms,
    load_seeds,
)
from ..profiles.store import ProfileStore
from ..tools.platform_resolver import (
    resolve_podcast_query,
    resolve_social_handle,
    resolve_twitch_login,
    resolve_youtube_handle,
)


class DebateCommandTool(BaseTool):
    """Expose debate analysis features through simple commands."""

    name: str = "Debate Command Tool"
    description: str = "Run debate analysis, context lookup and leaderboard ops."
    model_config = {"extra": "allow"}

    def __init__(
        self,
        pipeline=None,  # type: ignore[annotation-unchecked]
        ethan_defender: Callable[[str], str] | None = None,
        hasan_defender: Callable[[str], str] | None = None,
        profile_store: ProfileStore | None = None,
    ):
        super().__init__()
        # Local import to avoid circular dependency at module import time.
        if pipeline is None:
            from ..debate_analysis_pipeline import DebateAnalysisPipeline

            pipeline = DebateAnalysisPipeline(
                ethan_defender=ethan_defender, hasan_defender=hasan_defender
            )
        self.pipeline = pipeline
        self.index = self.pipeline.index_tool
        self.fact_checker = self.pipeline.fact_checker
        self.leaderboard = self.pipeline.leaderboard
        self.timeline = self.pipeline.timeline
        self.trust_tracker = self.pipeline.trust_tracker
        self.profile_tool = self.pipeline.profile_tool
        self.profile_store = profile_store or ProfileStore(":memory:")

    def _run(self, command: str, **kwargs):
        if command == "analyze":
            return self.pipeline.analyze(
                kwargs["url"],
                kwargs.get("ts", 0.0),
                kwargs.get("clip_text", ""),
                kwargs.get("person", "unknown"),
                transcript=kwargs.get("transcript"),
            )
        if command == "context":
            context = self.index.get_context(kwargs["video_id"], kwargs.get("ts", 0.0))
            return {"status": "success", "context": context}
        if command == "claim":
            result = self.fact_checker.run(kwargs["claim"])
            if person := kwargs.get("person"):
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
            return result
        if command == "leaderboard":
            return {"status": "success", "results": self.leaderboard.get_top(kwargs.get("n", 10))}
        if command == "timeline":
            return {
                "status": "success",
                "events": self.timeline.get_timeline(kwargs["video_id"]),
            }
        if command == "profile" or command == "creator":
            return {
                "status": "success",
                "profile": self.profile_tool.get_profile(kwargs["person"]),
            }
        if command == "latest":
            prof = self.profile_tool.get_profile(kwargs["person"]) or {}
            events = prof.get("events", [])
            events = sorted(events, key=lambda e: e.get("ts", 0), reverse=True)
            return {"status": "success", "events": events[: kwargs.get("n", 5)]}
        if command == "collabs":
            collabs = self.profile_store.get_collaborators(kwargs["person"], kwargs.get("n", 10))
            return {"status": "success", "collabs": collabs}
        if command == "trends":
            return {"status": "success", "trends": []}
        if command == "compare":
            a = self.profile_store.get_collaborators(kwargs["a"], kwargs.get("n", 10))
            b = self.profile_store.get_collaborators(kwargs["b"], kwargs.get("n", 10))
            return {"status": "success", "compare": {kwargs["a"]: a, kwargs["b"]: b}}
        if command == "verify_profiles":
            seeds = load_seeds(kwargs.get("seeds", "profiles.yaml"))
            verified = []
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
                        getattr(platforms, social).append(
                            resolve_social_handle(social, handles[social][0])
                        )
                profile = CreatorProfile(
                    name=seed.name,
                    type=seed.type,
                    roles=seed.roles,
                    shows=seed.shows,
                    content_tags=seed.content_tags,
                    platforms=platforms,
                )
                self.profile_store.upsert_profile(profile)
                verified.append(seed.name)
            return {"status": "success", "verified": verified}
        return {"status": "error", "error": "unknown command"}

    def run(self, *args, **kwargs):  # pragma: no cover - thin wrapper
        return self._run(*args, **kwargs)
