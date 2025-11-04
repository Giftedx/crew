"""Lightweight pipeline for debate clip analysis."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, TypedDict

# Import tools via the package aggregator to honor the canonical module mapping
from .tools import (
    AudioTranscriptionTool,
    CharacterProfileTool,
    ContextVerificationTool,
    FactCheckTool,
    LeaderboardTool,
    MultiPlatformDownloadTool,
    TimelineTool,
    TranscriptIndexTool,
    TrustworthinessTrackerTool,
)


if TYPE_CHECKING:
    from collections.abc import Callable

    # Type-only import via aggregator; resolves to domains.memory.vector.memory_storage_tool
    from .tools import MemoryStorageTool


class DebateAnalysisPipeline:
    """Download, transcribe and analyse clips for context and accuracy."""

    def __init__(
        self,
        downloader: MultiPlatformDownloadTool | None = None,
        transcriber: AudioTranscriptionTool | None = None,
        index_tool: TranscriptIndexTool | None = None,
        context_tool: ContextVerificationTool | None = None,
        fact_checker: FactCheckTool | None = None,
        leaderboard: LeaderboardTool | None = None,
        timeline: TimelineTool | None = None,
        memory_storage: MemoryStorageTool | None = None,
        trust_tracker: TrustworthinessTrackerTool | None = None,
        profile_tool: CharacterProfileTool | None = None,
        ethan_defender: Callable[[str], str] | None = None,
        hasan_defender: Callable[[str], str] | None = None,
    ) -> None:
        self.downloader = downloader or MultiPlatformDownloadTool()
        self.transcriber = transcriber or AudioTranscriptionTool()
        self.index_tool = index_tool or TranscriptIndexTool()
        self.context_tool = context_tool or ContextVerificationTool(self.index_tool)
        self.fact_checker = fact_checker or FactCheckTool()
        self.leaderboard = leaderboard or LeaderboardTool()
        self.timeline = timeline or TimelineTool()
        self.memory_storage = memory_storage
        self.trust_tracker = trust_tracker or TrustworthinessTrackerTool()
        self.profile_tool = profile_tool or CharacterProfileTool(
            leaderboard=self.leaderboard, trust_tracker=self.trust_tracker
        )
        self.ethan_defender = ethan_defender
        self.hasan_defender = hasan_defender

    class DebateAnalysisResult(TypedDict, total=False):
        status: str
        context: str
        context_verdict: str
        fact_verdict: str
        evidence: list[Any]
        deltas: dict[str, int]
        ethan_defender: str
        hasan_defender: str
        clip: str  # include for compatibility with timeline/profile aggregation

    def analyze(
        self,
        url: str,
        ts: float,
        clip_text: str,
        person: str,
        transcript: str | None = None,
    ) -> DebateAnalysisResult:
        """Run context verification and fact-checking for a clip.

        Parameters
        ----------
        url: str
            Video URL or identifier.
        ts: float
            Timestamp of the clip in seconds.
        clip_text: str
            Text alleged to appear in the clip.
        person: str
            Person whose claim is being analysed.
        transcript: str, optional
            Pre-provided transcript to avoid downloading in tests.
        """
        video_id = url
        if transcript is None:
            download_info = self.downloader.run(url)
            video_id = download_info.get("id", url)
            local_path = download_info.get("local_path")
            if local_path:
                transcription = self.transcriber.run(local_path)
                transcript = str(transcription.get("transcript", ""))
            else:
                transcript = ""
        self.index_tool.index_transcript(transcript or "", video_id)
        context = self.context_tool.run(video_id=video_id, ts=ts, clip_text=clip_text)
        fact = self.fact_checker.run(clip_text)
        verdict = fact.get("verdict")
        lies = 1 if verdict == "false" else 0
        misquotes = 1 if context.get("verdict") == "missing-context" else 0
        misinfo = 1 if fact.get("evidence") else 0
        self.leaderboard.update_scores(person, lies, misquotes, misinfo)
        self.trust_tracker.run(person, verdict != "false")
        self.timeline.add_event(
            video_id,
            {
                "ts": ts,
                "clip": clip_text,
                "context_verdict": str(context.get("verdict", "")),
                "fact_verdict": str(fact.get("verdict", "")),
                "evidence": fact.get("evidence", []),
            },
        )
        self.profile_tool.record_event(
            person,
            {
                "video_id": video_id,
                "ts": ts,
                "clip": clip_text,
                "fact_verdict": str(verdict),
                "context_verdict": str(context.get("verdict", "")),
                "evidence": fact.get("evidence", []),
            },
        )
        if self.memory_storage is not None:
            self.memory_storage.run(
                context.get("context", ""),
                {
                    "video_id": video_id,
                    "ts": ts,
                    "person": person,
                    "clip_text": clip_text,
                    "fact_verdict": fact.get("verdict"),
                    "context_verdict": context.get("verdict"),
                },
                collection="analysis",
            )
        summary = f"clip: {clip_text}\ncontext_verdict: {context.get('verdict')} fact_verdict: {fact.get('verdict')}"
        if self.ethan_defender is not None:
            ethan_blurb = str(self.ethan_defender(summary))
        else:
            ethan_blurb = "Traitor AB: seems legit" if lies == 0 else "Traitor AB: sketchy vibes"
        if self.hasan_defender is not None:
            hasan_blurb = str(self.hasan_defender(summary))
        else:
            hasan_blurb = "Old Dan: rock solid" if lies == 0 else "Old Dan: nah that's cap"
        return {
            "status": "success",
            "context": context.get("context", ""),
            "context_verdict": context.get("verdict", "uncertain"),
            "fact_verdict": fact.get("verdict", "uncertain"),
            "evidence": fact.get("evidence", []),
            "deltas": {"lies": lies, "misquotes": misquotes, "misinfo": misinfo},
            "ethan_defender": ethan_blurb[:180],
            "hasan_defender": hasan_blurb[:180],
        }
