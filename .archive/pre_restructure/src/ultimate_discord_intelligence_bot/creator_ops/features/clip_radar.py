"""
Live Clip Radar for real-time stream monitoring and viral moment detection.

This module provides real-time monitoring of live streams with viral moment
detection, automatic clip generation, and stream marker creation.
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import TYPE_CHECKING, Any

from ultimate_discord_intelligence_bot.creator_ops.config import CreatorOpsConfig
from ultimate_discord_intelligence_bot.creator_ops.integrations.twitch_client import (
    TwitchClient,
)
from ultimate_discord_intelligence_bot.creator_ops.integrations.youtube_client import (
    YouTubeClient,
)
from ultimate_discord_intelligence_bot.creator_ops.media import (
    NLPPipeline,
    SpeakerDiarization,
    WhisperASR,
)
from ultimate_discord_intelligence_bot.creator_ops.media.alignment import (
    TranscriptAlignment,
)
from ultimate_discord_intelligence_bot.step_result import StepResult


if TYPE_CHECKING:
    from collections.abc import Callable


logger = logging.getLogger(__name__)


@dataclass
class ViralMoment:
    """Viral moment detected in live stream."""

    timestamp: datetime
    start_time: float
    end_time: float
    duration: float
    trigger_type: str  # chat_velocity, sentiment_flip, laughter, engagement_spike
    confidence: float
    chat_velocity: float | None = None
    sentiment_score: float | None = None
    laughter_indicators: list[str] | None = None
    engagement_metrics: dict[str, Any] | None = None


@dataclass
class ClipCandidate:
    """Generated clip candidate."""

    id: str
    title: str
    description: str
    start_time: float
    end_time: float
    duration: float
    viral_moment: ViralMoment
    transcript: str | None = None
    speakers: list[str] | None = None
    sentiment: str | None = None
    engagement_score: float | None = None
    thumbnail_url: str | None = None


@dataclass
class StreamMarker:
    """Stream marker for viral moment."""

    id: str
    description: str
    position_seconds: int
    created_at: datetime
    platform: str
    stream_id: str


class LiveClipRadar:
    """
    Live Clip Radar for real-time stream monitoring and viral moment detection.

    Features:
    - Real-time stream monitoring (YouTube LiveChat, Twitch EventSub)
    - Viral moment detection (chat velocity, sentiment flips, laughter)
    - Automatic clip generation with titles and hooks
    - Stream marker creation
    - Draft short video generation
    """

    def __init__(
        self,
        config: CreatorOpsConfig | None = None,
        youtube_client: YouTubeClient | None = None,
        twitch_client: TwitchClient | None = None,
    ) -> None:
        """Initialize Live Clip Radar."""
        self.config = config or CreatorOpsConfig()
        self.youtube_client = youtube_client or YouTubeClient(config=self.config)
        self.twitch_client = twitch_client or TwitchClient(config=self.config)

        # Media processing components
        self.asr = WhisperASR(config=self.config)
        self.diarization = SpeakerDiarization(config=self.config)
        self.alignment = TranscriptAlignment()
        self.nlp = NLPPipeline(config=self.config)

        # Monitoring state
        self.active_monitors = {}
        self.viral_moments = []
        self.clip_candidates = []
        self._background_tasks: set[asyncio.Task[Any]] = set()

    async def start_monitoring(
        self,
        stream_url: str,
        platform: str,
        creator_handle: str,
        detection_callback: Callable[[ViralMoment], None] | None = None,
    ) -> StepResult:
        """
        Start monitoring a live stream for viral moments.

        Args:
            stream_url: URL of the live stream
            platform: Platform (youtube, twitch)
            creator_handle: Creator's handle
            detection_callback: Callback function for viral moment detection

        Returns:
            StepResult with monitoring status
        """
        try:
            monitor_id = f"{platform}_{creator_handle}_{datetime.utcnow().timestamp()}"

            # Start platform-specific monitoring
            if platform.lower() == "youtube":
                result = await self._start_youtube_monitoring(stream_url, creator_handle, detection_callback)
            elif platform.lower() == "twitch":
                result = await self._start_twitch_monitoring(stream_url, creator_handle, detection_callback)
            else:
                return StepResult.fail(f"Unsupported platform: {platform}")

            if result.success:
                self.active_monitors[monitor_id] = {
                    "platform": platform,
                    "creator": creator_handle,
                    "start_time": datetime.utcnow(),
                    "status": "monitoring",
                }

                return StepResult.ok(
                    data={
                        "monitor_id": monitor_id,
                        "status": "started",
                        "platform": platform,
                        "creator": creator_handle,
                    }
                )
            else:
                return result

        except Exception as e:
            logger.error(f"Failed to start monitoring: {e!s}")
            return StepResult.fail(f"Failed to start monitoring: {e!s}")

    async def stop_monitoring(self, monitor_id: str) -> StepResult:
        """
        Stop monitoring a live stream.

        Args:
            monitor_id: Monitor identifier

        Returns:
            StepResult with stop status
        """
        try:
            if monitor_id not in self.active_monitors:
                return StepResult.fail(f"Monitor not found: {monitor_id}")

            # Stop monitoring
            monitor_info = self.active_monitors[monitor_id]
            platform = monitor_info["platform"]

            if platform == "youtube":
                # YouTube monitoring is handled by callback, just remove from active
                pass
            elif platform == "twitch":
                # Twitch monitoring might need explicit stop
                pass

            # Update monitor status
            self.active_monitors[monitor_id]["status"] = "stopped"
            self.active_monitors[monitor_id]["end_time"] = datetime.utcnow()

            return StepResult.ok(
                data={
                    "monitor_id": monitor_id,
                    "status": "stopped",
                    "duration": (datetime.utcnow() - monitor_info["start_time"]).total_seconds(),
                }
            )

        except Exception as e:
            logger.error(f"Failed to stop monitoring: {e!s}")
            return StepResult.fail(f"Failed to stop monitoring: {e!s}")

    async def _start_youtube_monitoring(
        self,
        stream_url: str,
        creator_handle: str,
        detection_callback: Callable[[ViralMoment], None] | None = None,
    ) -> StepResult:
        """Start YouTube live stream monitoring."""
        try:
            # Extract video ID from URL
            video_id = self._extract_youtube_video_id(stream_url)
            if not video_id:
                return StepResult.fail("Invalid YouTube stream URL")

            # Get live stream details
            live_details_result = self.youtube_client.get_live_stream_details(video_id)
            if not live_details_result.success:
                return live_details_result

            live_details = live_details_result.data
            live_chat_id = live_details.get("activeLiveChatId")

            if not live_chat_id:
                return StepResult.fail("No active live chat found")

            # Start live chat monitoring
            chat_callback = self._create_chat_callback(detection_callback, "youtube")

            # Monitor live chat for 60 minutes (configurable)
            monitor_result = await self.youtube_client.monitor_live_chat(
                live_chat_id=live_chat_id,
                callback=chat_callback,
                max_duration_minutes=60,
            )

            return monitor_result

        except Exception as e:
            logger.error(f"Failed to start YouTube monitoring: {e!s}")
            return StepResult.fail(f"Failed to start YouTube monitoring: {e!s}")

    async def _start_twitch_monitoring(
        self,
        stream_url: str,
        creator_handle: str,
        detection_callback: Callable[[ViralMoment], None] | None = None,
    ) -> StepResult:
        """Start Twitch live stream monitoring."""
        try:
            # Extract channel name from URL
            channel_name = self._extract_twitch_channel(stream_url)
            if not channel_name:
                return StepResult.fail("Invalid Twitch stream URL")

            # Get user info
            user_result = self.twitch_client.get_user(login=channel_name)
            if not user_result.success:
                return user_result

            user = user_result.data

            # Check if user is currently streaming
            streams_result = self.twitch_client.get_streams(user_id=user.id)
            if not streams_result.success:
                return streams_result

            streams = streams_result.data["streams"]
            if not streams:
                return StepResult.fail("User is not currently streaming")

            # Start EventSub monitoring
            event_callback = self._create_event_callback(detection_callback, "twitch")

            # Monitor for 60 minutes (configurable)
            monitor_result = await self.twitch_client.monitor_eventsub_websocket(
                callback=event_callback,
                max_duration_minutes=60,
            )

            return monitor_result

        except Exception as e:
            logger.error(f"Failed to start Twitch monitoring: {e!s}")
            return StepResult.fail(f"Failed to start Twitch monitoring: {e!s}")

    def _create_chat_callback(
        self,
        detection_callback: Callable[[ViralMoment], None] | None,
        platform: str,
    ) -> Callable:
        """Create callback for chat message processing."""
        chat_history = []
        last_analysis_time = datetime.utcnow()

        async def chat_callback(messages):
            nonlocal chat_history, last_analysis_time

            # Add new messages to history
            chat_history.extend(messages)

            # Keep only last 5 minutes of chat
            cutoff_time = datetime.utcnow() - timedelta(minutes=5)
            chat_history = [msg for msg in chat_history if msg.published_at > cutoff_time]

            # Analyze for viral moments every 30 seconds
            if datetime.utcnow() - last_analysis_time > timedelta(seconds=30):
                viral_moment = self._detect_viral_moment_from_chat(chat_history, platform)

                if viral_moment and detection_callback:
                    detection_callback(viral_moment)

                last_analysis_time = datetime.utcnow()

        return chat_callback

    def _create_event_callback(
        self,
        detection_callback: Callable[[ViralMoment], None] | None,
        platform: str,
    ) -> Callable:
        """Create callback for EventSub event processing."""
        event_history = []
        last_analysis_time = datetime.utcnow()

        async def event_callback(message):
            nonlocal event_history, last_analysis_time

            # Add new event to history
            event_history.append(message)

            # Keep only last 5 minutes of events
            cutoff_time = datetime.utcnow() - timedelta(minutes=5)
            event_history = [event for event in event_history if event.message_timestamp > cutoff_time]

            # Analyze for viral moments every 30 seconds
            if datetime.utcnow() - last_analysis_time > timedelta(seconds=30):
                viral_moment = self._detect_viral_moment_from_events(event_history, platform)

                if viral_moment and detection_callback:
                    detection_callback(viral_moment)

                last_analysis_time = datetime.utcnow()

        return event_callback

    def _detect_viral_moment_from_chat(
        self,
        chat_history: list,
        platform: str,
    ) -> ViralMoment | None:
        """Detect viral moment from chat history."""
        try:
            if len(chat_history) < 10:
                return None

            # Calculate chat velocity (messages per minute)
            now = datetime.utcnow()
            recent_messages = [msg for msg in chat_history if (now - msg.published_at).total_seconds() < 60]

            chat_velocity = len(recent_messages)

            # Check for velocity spike (>3x baseline)
            baseline_velocity = len(chat_history) / 5  # 5-minute window
            if chat_velocity > baseline_velocity * 3:
                # Detect laughter indicators
                laughter_indicators = self._detect_laughter_indicators(recent_messages)

                # Calculate sentiment
                sentiment_score = self._calculate_chat_sentiment(recent_messages)

                viral_moment = ViralMoment(
                    timestamp=now,
                    start_time=now.timestamp(),
                    end_time=now.timestamp() + 30,  # 30-second window
                    duration=30.0,
                    trigger_type="chat_velocity",
                    confidence=min(chat_velocity / (baseline_velocity * 3), 1.0),
                    chat_velocity=chat_velocity,
                    sentiment_score=sentiment_score,
                    laughter_indicators=laughter_indicators,
                    engagement_metrics={
                        "baseline_velocity": baseline_velocity,
                        "velocity_ratio": chat_velocity / baseline_velocity,
                    },
                )

                self.viral_moments.append(viral_moment)
                return viral_moment

            return None

        except Exception as e:
            logger.error(f"Failed to detect viral moment from chat: {e!s}")
            return None

    def _detect_viral_moment_from_events(
        self,
        event_history: list,
        platform: str,
    ) -> ViralMoment | None:
        """Detect viral moment from EventSub events."""
        try:
            if len(event_history) < 5:
                return None

            # Count recent events
            now = datetime.utcnow()
            recent_events = [event for event in event_history if (now - event.message_timestamp).total_seconds() < 60]

            event_count = len(recent_events)

            # Check for event spike
            baseline_events = len(event_history) / 5  # 5-minute window
            if event_count > baseline_events * 2:
                viral_moment = ViralMoment(
                    timestamp=now,
                    start_time=now.timestamp(),
                    end_time=now.timestamp() + 30,
                    duration=30.0,
                    trigger_type="engagement_spike",
                    confidence=min(event_count / (baseline_events * 2), 1.0),
                    engagement_metrics={
                        "baseline_events": baseline_events,
                        "event_ratio": event_count / baseline_events,
                        "event_types": [event.message_type for event in recent_events],
                    },
                )

                self.viral_moments.append(viral_moment)
                return viral_moment

            return None

        except Exception as e:
            logger.error(f"Failed to detect viral moment from events: {e!s}")
            return None

    def _detect_laughter_indicators(self, messages: list) -> list[str]:
        """Detect laughter indicators in chat messages."""
        laughter_keywords = [
            "lol",
            "lmao",
            "haha",
            "hahaha",
            "😂",
            "🤣",
            "😆",
            "😄",
            "rofl",
            "lolol",
            "hahahaha",
            "lmaooo",
            "dead",
            "dying",
        ]

        indicators = []
        for message in messages:
            text = message.display_message.lower()
            for keyword in laughter_keywords:
                if keyword in text:
                    indicators.append(keyword)

        return list(set(indicators))  # Remove duplicates

    def _calculate_chat_sentiment(self, messages: list) -> float:
        """Calculate sentiment score for chat messages."""
        try:
            if not messages:
                return 0.0

            # Simple sentiment analysis based on keywords
            positive_keywords = [
                "love",
                "amazing",
                "great",
                "awesome",
                "best",
                "fire",
                "🔥",
            ]
            negative_keywords = [
                "hate",
                "terrible",
                "awful",
                "worst",
                "trash",
                "boring",
            ]

            positive_count = 0
            negative_count = 0

            for message in messages:
                text = message.display_message.lower()
                for keyword in positive_keywords:
                    if keyword in text:
                        positive_count += 1
                for keyword in negative_keywords:
                    if keyword in text:
                        negative_count += 1

            total_sentiment_words = positive_count + negative_count
            if total_sentiment_words == 0:
                return 0.0

            # Return sentiment score (-1 to 1)
            return (positive_count - negative_count) / total_sentiment_words

        except Exception as e:
            logger.warning(f"Failed to calculate chat sentiment: {e!s}")
            return 0.0

    async def generate_clip_candidate(
        self,
        viral_moment: ViralMoment,
        stream_url: str,
        platform: str,
    ) -> StepResult:
        """
        Generate a clip candidate from a viral moment.

        Args:
            viral_moment: Detected viral moment
            stream_url: URL of the live stream
            platform: Platform (youtube, twitch)

        Returns:
            StepResult with clip candidate
        """
        try:
            # Extract audio for the viral moment window
            audio_path = await self._extract_audio_segment(stream_url, viral_moment.start_time, viral_moment.end_time)

            if not audio_path:
                return StepResult.fail("Failed to extract audio segment")

            # Transcribe the segment
            asr_result = self.asr.transcribe_audio(audio_path)
            if not asr_result.success:
                return asr_result

            # Perform diarization
            diarization_result = self.diarization.diarize_audio(audio_path)
            if not diarization_result.success:
                return diarization_result

            # Align transcripts
            alignment_result = self.alignment.align_transcripts(asr_result.data, diarization_result.data)
            if not alignment_result.success:
                return alignment_result

            # Perform NLP analysis
            nlp_result = self.nlp.analyze_transcript(alignment_result.data)
            if not nlp_result.success:
                return nlp_result

            # Generate title and description
            title_result = self._generate_clip_title(alignment_result.data, nlp_result.data, viral_moment)
            description_result = self._generate_clip_description(alignment_result.data, nlp_result.data, viral_moment)

            # Create clip candidate
            clip_id = f"clip_{viral_moment.timestamp.timestamp()}"
            clip_candidate = ClipCandidate(
                id=clip_id,
                title=title_result,
                description=description_result,
                start_time=viral_moment.start_time,
                end_time=viral_moment.end_time,
                duration=viral_moment.duration,
                viral_moment=viral_moment,
                transcript=alignment_result.data.segments[0].text if alignment_result.data.segments else None,
                speakers=[seg.speaker for seg in alignment_result.data.segments if seg.speaker],
                sentiment=nlp_result.data.sentiment_analysis[0].label if nlp_result.data.sentiment_analysis else None,
                engagement_score=viral_moment.confidence,
            )

            self.clip_candidates.append(clip_candidate)

            return StepResult.ok(data=clip_candidate)

        except Exception as e:
            logger.error(f"Failed to generate clip candidate: {e!s}")
            return StepResult.fail(f"Failed to generate clip candidate: {e!s}")

    async def create_stream_marker(
        self,
        viral_moment: ViralMoment,
        platform: str,
        stream_id: str,
    ) -> StepResult:
        """
        Create a stream marker for a viral moment.

        Args:
            viral_moment: Detected viral moment
            platform: Platform (youtube, twitch)
            stream_id: Stream identifier

        Returns:
            StepResult with stream marker
        """
        try:
            description = f"Viral moment: {viral_moment.trigger_type} (confidence: {viral_moment.confidence:.2f})"
            position_seconds = int(viral_moment.start_time)

            if platform.lower() == "twitch":
                # Create Twitch stream marker
                marker_result = self.twitch_client.create_stream_marker(user_id=stream_id, description=description)

                if marker_result.success:
                    marker_data = marker_result.data
                    stream_marker = StreamMarker(
                        id=marker_data.id,
                        description=description,
                        position_seconds=position_seconds,
                        created_at=datetime.utcnow(),
                        platform="twitch",
                        stream_id=stream_id,
                    )

                    return StepResult.ok(data=stream_marker)
                else:
                    return marker_result

            elif platform.lower() == "youtube":
                # YouTube doesn't have direct stream markers, but we can log the moment
                stream_marker = StreamMarker(
                    id=f"youtube_marker_{viral_moment.timestamp.timestamp()}",
                    description=description,
                    position_seconds=position_seconds,
                    created_at=datetime.utcnow(),
                    platform="youtube",
                    stream_id=stream_id,
                )

                return StepResult.ok(data=stream_marker)

            else:
                return StepResult.fail(f"Unsupported platform for stream markers: {platform}")

        except Exception as e:
            logger.error(f"Failed to create stream marker: {e!s}")
            return StepResult.fail(f"Failed to create stream marker: {e!s}")

    def _extract_youtube_video_id(self, url: str) -> str | None:
        """Extract YouTube video ID from URL."""
        import re

        patterns = [
            r"(?:youtube\.com/watch\?v=|youtu\.be/|youtube\.com/embed/)([^&\n?#]+)",
            r"youtube\.com/live/([^&\n?#]+)",
        ]

        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)

        return None

    def _extract_twitch_channel(self, url: str) -> str | None:
        """Extract Twitch channel name from URL."""
        import re

        pattern = r"twitch\.tv/([^/\n?#]+)"
        match = re.search(pattern, url)

        if match:
            return match.group(1)

        return None

    async def _extract_audio_segment(
        self,
        stream_url: str,
        start_time: float,
        end_time: float,
    ) -> str | None:
        """Extract audio segment from stream."""
        try:
            # This would use FFmpeg to extract audio segment
            # For now, return a placeholder path
            import os
            import tempfile

            # Calculate duration for the clip
            duration = max(0.0, float(end_time) - float(start_time))

            # Use a context manager for temp file creation per lint guidance
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
                temp_path = temp_file.name

            # Implemented: FFmpeg audio extraction
            try:
                import subprocess

                # Build FFmpeg command
                cmd = [
                    "ffmpeg",
                    "-i",
                    stream_url,
                    "-ss",
                    str(start_time),
                    "-t",
                    str(duration),
                    "-vn",  # No video
                    "-acodec",
                    "pcm_s16le",  # Audio codec
                    "-y",  # Overwrite output file
                    temp_path,
                ]

                # Execute FFmpeg command
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

                if result.returncode == 0:
                    logger.info(f"Audio extracted successfully: {temp_path}")
                    return temp_path if os.path.exists(temp_path) else None
                else:
                    logger.error(f"FFmpeg failed: {result.stderr}")
                    return None

            except subprocess.TimeoutExpired:
                logger.error("FFmpeg extraction timed out")
                return None
            except Exception as e:
                logger.error(f"FFmpeg extraction failed: {e}")
                return None

        except Exception as e:
            logger.error(f"Failed to extract audio segment: {e!s}")
            return None

    def _generate_clip_title(
        self,
        transcript: Any,
        nlp_result: Any,
        viral_moment: ViralMoment,
    ) -> str:
        """Generate title for clip candidate."""
        try:
            # Simple title generation based on transcript and viral moment
            if transcript.segments:
                first_segment = transcript.segments[0]
                text = first_segment.text[:50]  # First 50 characters

                # Add viral moment context
                if viral_moment.trigger_type == "chat_velocity":
                    return f"🔥 VIRAL MOMENT: {text}..."
                elif viral_moment.trigger_type == "laughter":
                    return f"😂 FUNNY MOMENT: {text}..."
                else:
                    return f"⚡ EPIC MOMENT: {text}..."

            return f"Viral Moment - {viral_moment.trigger_type}"

        except Exception as e:
            logger.warning(f"Failed to generate clip title: {e!s}")
            return f"Viral Moment - {viral_moment.trigger_type}"

    def _generate_clip_description(
        self,
        transcript: Any,
        nlp_result: Any,
        viral_moment: ViralMoment,
    ) -> str:
        """Generate description for clip candidate."""
        try:
            description = "Viral moment detected during live stream!\n\n"
            description += f"Trigger: {viral_moment.trigger_type}\n"
            description += f"Confidence: {viral_moment.confidence:.2f}\n"
            description += f"Duration: {viral_moment.duration:.1f} seconds\n\n"

            if transcript.segments:
                description += "Transcript:\n"
                for segment in transcript.segments[:3]:  # First 3 segments
                    if segment.speaker:
                        description += f"[{segment.speaker}]: {segment.text}\n"
                    else:
                        description += f"{segment.text}\n"

            return description

        except Exception as e:
            logger.warning(f"Failed to generate clip description: {e!s}")
            return f"Viral moment detected: {viral_moment.trigger_type}"

    def get_monitoring_status(self) -> dict[str, Any]:
        """Get current monitoring status."""
        return {
            "active_monitors": len([m for m in self.active_monitors.values() if m["status"] == "monitoring"]),
            "total_viral_moments": len(self.viral_moments),
            "total_clip_candidates": len(self.clip_candidates),
            "monitors": self.active_monitors,
        }

    def cleanup(self) -> None:
        """Cleanup resources."""
        # Stop all active monitors
        for monitor_id in list(self.active_monitors.keys()):
            task = asyncio.create_task(self.stop_monitoring(monitor_id))
            self._background_tasks.add(task)
            task.add_done_callback(self._background_tasks.discard)

        # Cleanup media processing components
        self.asr.cleanup()
        self.diarization.cleanup()
        self.nlp.cleanup()
