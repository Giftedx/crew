"""Lightweight pipeline for debate clip analysis."""
from __future__ import annotations

from typing import Callable, Optional

from .tools.yt_dlp_download_tool import YtDlpDownloadTool, YouTubeDownloadTool
from .tools.audio_transcription_tool import AudioTranscriptionTool
from .tools.transcript_index_tool import TranscriptIndexTool
from .tools.context_verification_tool import ContextVerificationTool
from .tools.fact_check_tool import FactCheckTool
from .tools.leaderboard_tool import LeaderboardTool
from .tools.timeline_tool import TimelineTool
from .tools.memory_storage_tool import MemoryStorageTool
from .tools.trustworthiness_tracker_tool import TrustworthinessTrackerTool
from .tools.character_profile_tool import CharacterProfileTool


class DebateAnalysisPipeline:
    """Download, transcribe and analyse clips for context and accuracy."""

    def __init__(
        self,
        downloader: Optional[YtDlpDownloadTool] = None,
        transcriber: Optional[AudioTranscriptionTool] = None,
        index_tool: Optional[TranscriptIndexTool] = None,
        context_tool: Optional[ContextVerificationTool] = None,
        fact_checker: Optional[FactCheckTool] = None,
        leaderboard: Optional[LeaderboardTool] = None,
        timeline: Optional[TimelineTool] = None,
        memory_storage: Optional[MemoryStorageTool] = None,
        trust_tracker: Optional[TrustworthinessTrackerTool] = None,
        profile_tool: Optional[CharacterProfileTool] = None,
        ethan_defender: Optional[Callable[[str], str]] = None,
        hasan_defender: Optional[Callable[[str], str]] = None,
    ) -> None:
        self.downloader = downloader or YouTubeDownloadTool()
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

    def analyze(
        self,
        url: str,
        ts: float,
        clip_text: str,
        person: str,
        transcript: str | None = None,
    ) -> dict:
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
                transcript = transcription.get("transcript", "")
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
                "context_verdict": context.get("verdict"),
                "fact_verdict": fact.get("verdict"),
                "evidence": fact.get("evidence", []),
            },
        )
        self.profile_tool.record_event(
            person,
            {
                "video_id": video_id,
                "ts": ts,
                "clip": clip_text,
                "fact_verdict": verdict,
                "context_verdict": context.get("verdict"),
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
        summary = (
            f"clip: {clip_text}\n"
            f"context_verdict: {context.get('verdict')}"
            f" fact_verdict: {fact.get('verdict')}"
        )
        if self.ethan_defender is not None:
            ethan_blurb = str(self.ethan_defender(summary))
        else:
            ethan_blurb = (
                "Traitor AB: seems legit"
                if lies == 0
                else "Traitor AB: sketchy vibes"
            )
        if self.hasan_defender is not None:
            hasan_blurb = str(self.hasan_defender(summary))
        else:
            hasan_blurb = (
                "Old Dan: rock solid" if lies == 0 else "Old Dan: nah that's cap"
            )
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
