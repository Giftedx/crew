"""
Live Clip Radar for real-time stream monitoring and viral moment detection.
Provides automatic detection of viral moments and clip generation for live streams.
"""

import asyncio
import contextlib
import logging
import re
import uuid
from collections import defaultdict, deque
from collections.abc import Callable
from datetime import datetime, timedelta

from ultimate_discord_intelligence_bot.creator_ops.config import CreatorOpsConfig
from ultimate_discord_intelligence_bot.creator_ops.features.clip_radar_models import (
    ChatMessage,
    ClipCandidate,
    ClipStatus,
    MomentType,
    MonitoringConfig,
    PlatformType,
    SentimentScore,
    StreamInfo,
    StreamStatus,
    ViralMoment,
)
from ultimate_discord_intelligence_bot.creator_ops.integrations.twitch_client import (
    TwitchClient,
)
from ultimate_discord_intelligence_bot.creator_ops.integrations.youtube_client import (
    YouTubeClient,
)
from ultimate_discord_intelligence_bot.creator_ops.media.alignment import (
    TranscriptAlignment,
)
from ultimate_discord_intelligence_bot.creator_ops.media.asr import WhisperASR
from ultimate_discord_intelligence_bot.creator_ops.media.diarization import (
    SpeakerDiarization,
)
from ultimate_discord_intelligence_bot.creator_ops.media.nlp import NLPPipeline
from ultimate_discord_intelligence_bot.step_result import StepResult


logger = logging.getLogger(__name__)


class LiveClipRadar:
    """Main class for Live Clip Radar functionality."""

    def __init__(self, config: CreatorOpsConfig):
        self.config = config
        self.youtube_client = YouTubeClient(config)
        self.twitch_client = TwitchClient(config)
        self.asr_processor = WhisperASR(config)
        self.diarization = SpeakerDiarization(config)
        self.alignment = TranscriptAlignment(config)
        self.nlp_pipeline = NLPPipeline(config)

        # Monitoring state
        self.monitoring_configs: dict[str, MonitoringConfig] = {}
        self.active_streams: dict[str, StreamInfo] = {}
        self.chat_queues: dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        self.sentiment_history: dict[str, deque] = defaultdict(lambda: deque(maxlen=100))
        self.monitoring_tasks: dict[str, asyncio.Task] = {}
        self.viral_moments: list[ViralMoment] = []
        self.clip_candidates: list[ClipCandidate] = []

        # Detection algorithms
        self.baseline_metrics: dict[str, dict[str, float]] = defaultdict(dict)
        self.moment_callbacks: list[Callable[[ViralMoment], None]] = []
        self.clip_callbacks: list[Callable[[ClipCandidate], None]] = []

    async def start_monitoring(
        self,
        config: MonitoringConfig,
        on_moment_detected: Callable[[ViralMoment], None] | None = None,
        on_clip_generated: Callable[[ClipCandidate], None] | None = None,
    ) -> StepResult:
        """
        Start monitoring a stream for viral moments.

        Args:
            config: Monitoring configuration
            on_moment_detected: Callback for detected viral moments
            on_clip_generated: Callback for generated clips

        Returns:
            StepResult with monitoring status
        """
        try:
            stream_key = f"{config.platform.value}_{config.channel_id}"

            if stream_key in self.monitoring_tasks:
                return StepResult.fail(f"Already monitoring {stream_key}")

            # Add callbacks
            if on_moment_detected:
                self.moment_callbacks.append(on_moment_detected)
            if on_clip_generated:
                self.clip_callbacks.append(on_clip_generated)

            # Store config
            self.monitoring_configs[stream_key] = config

            # Get stream info
            stream_info_result = await self._get_stream_info(config.platform, config.channel_id)
            if not stream_info_result.success:
                return StepResult.fail(f"Failed to get stream info: {stream_info_result.error}")

            stream_info = stream_info_result.data["stream_info"]
            self.active_streams[stream_key] = stream_info

            # Start monitoring task
            monitoring_task = asyncio.create_task(self._monitor_stream(stream_key, config, stream_info))
            self.monitoring_tasks[stream_key] = monitoring_task

            logger.info(f"Started monitoring {stream_key}")
            return StepResult.ok(data={"stream_key": stream_key, "stream_info": stream_info})

        except Exception as e:
            logger.error(f"Failed to start monitoring: {e!s}")
            return StepResult.fail(f"Failed to start monitoring: {e!s}")

    async def stop_monitoring(self, stream_key: str) -> StepResult:
        """
        Stop monitoring a stream.

        Args:
            stream_key: Stream identifier

        Returns:
            StepResult with stop status
        """
        try:
            if stream_key not in self.monitoring_tasks:
                return StepResult.fail(f"Not monitoring {stream_key}")

            # Cancel monitoring task
            task = self.monitoring_tasks[stream_key]
            task.cancel()

            with contextlib.suppress(asyncio.CancelledError):
                await task

            # Cleanup
            del self.monitoring_tasks[stream_key]
            if stream_key in self.monitoring_configs:
                del self.monitoring_configs[stream_key]
            if stream_key in self.active_streams:
                del self.active_streams[stream_key]

            # Clear queues
            if stream_key in self.chat_queues:
                del self.chat_queues[stream_key]
            if stream_key in self.sentiment_history:
                del self.sentiment_history[stream_key]

            logger.info(f"Stopped monitoring {stream_key}")
            return StepResult.ok(data={"stream_key": stream_key})

        except Exception as e:
            logger.error(f"Failed to stop monitoring: {e!s}")
            return StepResult.fail(f"Failed to stop monitoring: {e!s}")

    async def _monitor_stream(self, stream_key: str, config: MonitoringConfig, stream_info: StreamInfo) -> None:
        """Monitor a stream for viral moments."""
        try:
            logger.info(f"Starting stream monitoring for {stream_key}")

            if config.platform == PlatformType.YOUTUBE:
                await self._monitor_youtube_stream(stream_key, config, stream_info)
            elif config.platform == PlatformType.TWITCH:
                await self._monitor_twitch_stream(stream_key, config, stream_info)
            else:
                logger.error(f"Unsupported platform: {config.platform}")

        except asyncio.CancelledError:
            logger.info(f"Stream monitoring cancelled for {stream_key}")
        except Exception as e:
            logger.error(f"Stream monitoring failed for {stream_key}: {e!s}")

    async def _monitor_youtube_stream(self, stream_key: str, config: MonitoringConfig, stream_info: StreamInfo) -> None:
        """Monitor YouTube live stream."""
        try:
            # Get live chat messages
            chat_result = await self.youtube_client.get_live_chat_messages(stream_info.stream_id, max_results=200)

            if not chat_result.success:
                logger.error(f"Failed to get YouTube live chat: {chat_result.error}")
                return

            # Process chat messages
            for message_data in chat_result.data.get("messages", []):
                chat_message = ChatMessage(
                    message_id=message_data.get("id", ""),
                    user_id=message_data.get("authorChannelId", ""),
                    username=message_data.get("authorDisplayName", ""),
                    message=message_data.get("displayMessage", ""),
                    timestamp=datetime.fromisoformat(message_data.get("publishedAt", "").replace("Z", "+00:00")),
                    platform=PlatformType.YOUTUBE,
                    channel_id=config.channel_id,
                    stream_id=stream_info.stream_id,
                    emotes=self._extract_emotes(message_data.get("displayMessage", "")),
                    metadata=message_data,
                )

                await self._process_chat_message(stream_key, chat_message, config)

            # Continue monitoring
            await asyncio.sleep(5)  # Poll every 5 seconds

        except Exception as e:
            logger.error(f"YouTube stream monitoring error: {e!s}")

    async def _monitor_twitch_stream(self, stream_key: str, config: MonitoringConfig, stream_info: StreamInfo) -> None:
        """Monitor Twitch live stream."""
        try:
            # Get chat messages via EventSub
            # This would integrate with the Twitch EventSub WebSocket
            # For now, we'll simulate with periodic API calls

            chat_result = await self.twitch_client.get_chat_messages(config.channel_id, limit=100)

            if not chat_result.success:
                logger.error(f"Failed to get Twitch chat: {chat_result.error}")
                return

            # Process chat messages
            for message_data in chat_result.data.get("messages", []):
                chat_message = ChatMessage(
                    message_id=message_data.get("id", ""),
                    user_id=message_data.get("user_id", ""),
                    username=message_data.get("username", ""),
                    message=message_data.get("message", ""),
                    timestamp=datetime.fromisoformat(message_data.get("timestamp", "").replace("Z", "+00:00")),
                    platform=PlatformType.TWITCH,
                    channel_id=config.channel_id,
                    stream_id=stream_info.stream_id,
                    emotes=self._extract_emotes(message_data.get("message", "")),
                    badges=message_data.get("badges", []),
                    metadata=message_data,
                )

                await self._process_chat_message(stream_key, chat_message, config)

            # Continue monitoring
            await asyncio.sleep(3)  # Poll every 3 seconds

        except Exception as e:
            logger.error(f"Twitch stream monitoring error: {e!s}")

    async def _process_chat_message(self, stream_key: str, message: ChatMessage, config: MonitoringConfig) -> None:
        """Process a chat message for viral moment detection."""
        try:
            # Add to chat queue
            self.chat_queues[stream_key].append(message)

            # Analyze sentiment
            sentiment = await self._analyze_sentiment(message.message)

            # Add to sentiment history
            self.sentiment_history[stream_key].append(
                {
                    "timestamp": message.timestamp,
                    "sentiment": sentiment.score,
                    "message": message.message,
                }
            )

            # Check for viral moments
            await self._check_viral_moments(stream_key, message, sentiment, config)

        except Exception as e:
            logger.error(f"Failed to process chat message: {e!s}")

    async def _check_viral_moments(
        self,
        stream_key: str,
        trigger_message: ChatMessage,
        sentiment: SentimentScore,
        config: MonitoringConfig,
    ) -> None:
        """Check for viral moments based on chat analysis."""
        try:
            # Check chat velocity
            velocity_moment = await self._check_chat_velocity(stream_key, trigger_message, config)
            if velocity_moment:
                await self._handle_viral_moment(velocity_moment, config)

            # Check sentiment flip
            sentiment_moment = await self._check_sentiment_flip(stream_key, trigger_message, sentiment, config)
            if sentiment_moment:
                await self._handle_viral_moment(sentiment_moment, config)

            # Check laughter
            laughter_moment = await self._check_laughter(stream_key, trigger_message, config)
            if laughter_moment:
                await self._handle_viral_moment(laughter_moment, config)

        except Exception as e:
            logger.error(f"Failed to check viral moments: {e!s}")

    async def _check_chat_velocity(
        self, stream_key: str, trigger_message: ChatMessage, config: MonitoringConfig
    ) -> ViralMoment | None:
        """Check for chat velocity spikes."""
        try:
            chat_queue = self.chat_queues[stream_key]

            # Calculate current velocity (messages per minute)
            now = trigger_message.timestamp
            one_minute_ago = now - timedelta(minutes=1)

            recent_messages = [msg for msg in chat_queue if msg.timestamp >= one_minute_ago]
            current_velocity = len(recent_messages)

            # Calculate baseline velocity
            baseline = self._calculate_baseline_velocity(stream_key)

            # Check for spike
            if baseline > 0 and current_velocity > baseline * config.chat_velocity_threshold:
                velocity_ratio = current_velocity / baseline

                moment = ViralMoment(
                    moment_id=str(uuid.uuid4()),
                    moment_type=MomentType.CHAT_VELOCITY,
                    timestamp=trigger_message.timestamp,
                    platform=trigger_message.platform,
                    channel_id=trigger_message.channel_id,
                    stream_id=trigger_message.stream_id,
                    confidence=min(1.0, velocity_ratio / config.chat_velocity_threshold),
                    trigger_message=trigger_message,
                    context_messages=list(recent_messages[-10:]),  # Last 10 messages
                    metrics={
                        "current_velocity": current_velocity,
                        "baseline_velocity": baseline,
                        "velocity_ratio": velocity_ratio,
                    },
                    description=f"Chat velocity spike: {current_velocity} messages/min (baseline: {baseline:.1f})",
                )

                return moment

            return None

        except Exception as e:
            logger.error(f"Failed to check chat velocity: {e!s}")
            return None

    async def _check_sentiment_flip(
        self,
        stream_key: str,
        trigger_message: ChatMessage,
        current_sentiment: SentimentScore,
        config: MonitoringConfig,
    ) -> ViralMoment | None:
        """Check for sentiment flips."""
        try:
            sentiment_history = self.sentiment_history[stream_key]

            if len(sentiment_history) < 10:
                return None

            # Get recent sentiment trend
            recent_sentiments = [entry["sentiment"] for entry in list(sentiment_history)[-10:]]
            avg_recent = sum(recent_sentiments) / len(recent_sentiments)

            # Get older sentiment trend
            older_sentiments = [entry["sentiment"] for entry in list(sentiment_history)[-20:-10]]
            if len(older_sentiments) < 5:
                return None

            avg_older = sum(older_sentiments) / len(older_sentiments)

            # Check for significant flip
            sentiment_change = abs(avg_recent - avg_older)
            if sentiment_change > config.sentiment_flip_threshold:
                # Determine flip direction
                flip_type = "positive_surge" if avg_recent > avg_older else "negative_surge"

                moment = ViralMoment(
                    moment_id=str(uuid.uuid4()),
                    moment_type=MomentType.SENTIMENT_FLIP,
                    timestamp=trigger_message.timestamp,
                    platform=trigger_message.platform,
                    channel_id=trigger_message.channel_id,
                    stream_id=trigger_message.stream_id,
                    confidence=min(1.0, sentiment_change / config.sentiment_flip_threshold),
                    trigger_message=trigger_message,
                    context_messages=list(self.chat_queues[stream_key])[-10:],
                    metrics={
                        "sentiment_change": sentiment_change,
                        "previous_avg": avg_older,
                        "current_avg": avg_recent,
                        "flip_type": flip_type,
                    },
                    description=f"Sentiment flip: {flip_type} (change: {sentiment_change:.2f})",
                )

                return moment

            return None

        except Exception as e:
            logger.error(f"Failed to check sentiment flip: {e!s}")
            return None

    async def _check_laughter(
        self, stream_key: str, trigger_message: ChatMessage, config: MonitoringConfig
    ) -> ViralMoment | None:
        """Check for laughter indicators."""
        try:
            message_lower = trigger_message.message.lower()

            # Check for laughter keywords
            laughter_count = 0
            for keyword in config.laughter_keywords:
                laughter_count += message_lower.count(keyword.lower())

            # Check for repeated characters (hahaha, lololol, etc.)
            repeated_patterns = re.findall(r"(.)\1{2,}", message_lower)
            laughter_count += len(repeated_patterns)

            # Check for emoji patterns
            emoji_patterns = re.findall(r"[😂🤣😆😄😃😀]", trigger_message.message)
            laughter_count += len(emoji_patterns)

            if laughter_count > 0:
                # Check for laughter in recent messages
                recent_messages = list(self.chat_queues[stream_key])[-20:]
                total_laughter = 0

                for msg in recent_messages:
                    msg_lower = msg.message.lower()
                    for keyword in config.laughter_keywords:
                        total_laughter += msg_lower.count(keyword.lower())

                # Calculate confidence based on laughter intensity
                confidence = min(1.0, laughter_count / 5.0)  # Normalize to 0-1

                if confidence > config.detection_sensitivity:
                    moment = ViralMoment(
                        moment_id=str(uuid.uuid4()),
                        moment_type=MomentType.LAUGHTER,
                        timestamp=trigger_message.timestamp,
                        platform=trigger_message.platform,
                        channel_id=trigger_message.channel_id,
                        stream_id=trigger_message.stream_id,
                        confidence=confidence,
                        trigger_message=trigger_message,
                        context_messages=list(recent_messages[-5:]),
                        metrics={
                            "laughter_count": laughter_count,
                            "total_laughter": total_laughter,
                            "laughter_keywords": config.laughter_keywords,
                        },
                        description=f"Laughter detected: {laughter_count} indicators in recent messages",
                    )

                    return moment

            return None

        except Exception as e:
            logger.error(f"Failed to check laughter: {e!s}")
            return None

    async def _handle_viral_moment(self, moment: ViralMoment, config: MonitoringConfig) -> None:
        """Handle a detected viral moment."""
        try:
            logger.info(f"Viral moment detected: {moment.moment_type.value} at {moment.timestamp}")

            # Store the moment
            self.viral_moments.append(moment)

            # Generate clip candidate if enabled
            if config.auto_generate_clips:
                clip_candidate = await self._generate_clip_candidate(moment, config)
                if clip_candidate:
                    self.clip_candidates.append(clip_candidate)

                    # Call clip callbacks
                    for callback in self.clip_callbacks:
                        try:
                            callback(clip_candidate)
                        except Exception as e:
                            logger.error(f"Clip callback failed: {e!s}")

            # Create stream marker if enabled
            if config.auto_create_markers:
                await self._create_stream_marker(moment, config)

            # Call moment callbacks
            for callback in self.moment_callbacks:
                try:
                    callback(moment)
                except Exception as e:
                    logger.error(f"Moment callback failed: {e!s}")

        except Exception as e:
            logger.error(f"Failed to handle viral moment: {e!s}")

    async def _generate_clip_candidate(self, moment: ViralMoment, config: MonitoringConfig) -> ClipCandidate | None:
        """Generate a clip candidate from a viral moment."""
        try:
            # Calculate clip timing
            clip_duration = min(max(config.min_clip_duration, 30.0), config.max_clip_duration)
            start_time = max(0, moment.timestamp.timestamp() - clip_duration / 2)
            end_time = start_time + clip_duration

            # Generate title and description
            title = await self._generate_clip_title(moment)
            description = await self._generate_clip_description(moment)

            clip_candidate = ClipCandidate(
                clip_id=str(uuid.uuid4()),
                moment_id=moment.moment_id,
                title=title,
                description=description,
                start_time=start_time,
                end_time=end_time,
                duration=clip_duration,
                platform=moment.platform,
                stream_id=moment.stream_id,
                channel_id=moment.channel_id,
                status=ClipStatus.DETECTED,
                viral_moment=moment,
                metadata={
                    "moment_type": moment.moment_type.value,
                    "confidence": moment.confidence,
                    "trigger_message": moment.trigger_message.message if moment.trigger_message else "",
                },
            )

            logger.info(f"Generated clip candidate: {clip_candidate.title}")
            return clip_candidate

        except Exception as e:
            logger.error(f"Failed to generate clip candidate: {e!s}")
            return None

    async def _create_stream_marker(self, moment: ViralMoment, config: MonitoringConfig) -> None:
        """Create a stream marker for a viral moment."""
        try:
            if moment.platform == PlatformType.TWITCH:
                # Create Twitch stream marker
                marker_result = await self.twitch_client.create_stream_marker(
                    user_id=config.channel_id,
                    description=f"Viral moment: {moment.moment_type.value} - {moment.description}",
                )

                if marker_result.success:
                    logger.info(f"Created Twitch stream marker for {moment.moment_id}")
                else:
                    logger.error(f"Failed to create Twitch marker: {marker_result.error}")

            elif moment.platform == PlatformType.YOUTUBE:
                # YouTube doesn't have direct marker API, but we can log the timestamp
                logger.info(f"YouTube viral moment at {moment.timestamp}: {moment.description}")

        except Exception as e:
            logger.error(f"Failed to create stream marker: {e!s}")

    async def _generate_clip_title(self, moment: ViralMoment) -> str:
        """Generate a clip title based on the viral moment."""
        try:
            moment_type_titles = {
                MomentType.CHAT_VELOCITY: "Chat Goes Wild!",
                MomentType.SENTIMENT_FLIP: "Mood Shift Moment",
                MomentType.LAUGHTER: "Hilarious Moment",
                MomentType.EMOTIONAL_PEAK: "Emotional Peak",
                MomentType.CONTROVERSY: "Controversial Moment",
                MomentType.BREAKING_NEWS: "Breaking News",
            }

            base_title = moment_type_titles.get(moment.moment_type, "Viral Moment")

            # Add context if available
            if moment.trigger_message:
                # Extract key words from trigger message
                words = moment.trigger_message.message.split()[:3]
                context = " ".join(words)
                if len(context) > 20:
                    context = context[:20] + "..."
                return f"{base_title}: {context}"

            return base_title

        except Exception as e:
            logger.error(f"Failed to generate clip title: {e!s}")
            return "Viral Moment"

    async def _generate_clip_description(self, moment: ViralMoment) -> str:
        """Generate a clip description based on the viral moment."""
        try:
            description_parts = [
                f"Detected viral moment: {moment.moment_type.value}",
                f"Confidence: {moment.confidence:.1%}",
                f"Timestamp: {moment.timestamp.strftime('%H:%M:%S')}",
            ]

            if moment.trigger_message:
                description_parts.append(f"Trigger: {moment.trigger_message.message[:100]}")

            return " | ".join(description_parts)

        except Exception as e:
            logger.error(f"Failed to generate clip description: {e!s}")
            return "Viral moment detected during live stream"

    async def _get_stream_info(self, platform: PlatformType, channel_id: str) -> StepResult:
        """Get information about a live stream."""
        try:
            if platform == PlatformType.YOUTUBE:
                # Get YouTube live stream info
                stream_result = await self.youtube_client.get_live_stream(channel_id)
                if not stream_result.success:
                    return StepResult.fail(f"Failed to get YouTube stream: {stream_result.error}")

                stream_data = stream_result.data["stream"]
                stream_info = StreamInfo(
                    stream_id=stream_data.get("id", ""),
                    channel_id=channel_id,
                    platform=platform,
                    title=stream_data.get("snippet", {}).get("title", ""),
                    description=stream_data.get("snippet", {}).get("description", ""),
                    status=StreamStatus.ONLINE,
                    started_at=datetime.fromisoformat(
                        stream_data.get("snippet", {}).get("publishedAt", "").replace("Z", "+00:00")
                    ),
                    viewer_count=stream_data.get("liveStreamingDetails", {}).get("concurrentViewers", 0),
                    language=stream_data.get("snippet", {}).get("defaultLanguage", "en"),
                    category=stream_data.get("snippet", {}).get("categoryId", ""),
                    metadata=stream_data,
                )

            elif platform == PlatformType.TWITCH:
                # Get Twitch stream info
                stream_result = await self.twitch_client.get_stream(user_id=channel_id)
                if not stream_result.success:
                    return StepResult.fail(f"Failed to get Twitch stream: {stream_result.error}")

                stream_data = stream_result.data["stream"]
                stream_info = StreamInfo(
                    stream_id=stream_data.get("id", ""),
                    channel_id=channel_id,
                    platform=platform,
                    title=stream_data.get("title", ""),
                    description=stream_data.get("description", ""),
                    status=StreamStatus.ONLINE,
                    started_at=datetime.fromisoformat(stream_data.get("started_at", "").replace("Z", "+00:00")),
                    viewer_count=stream_data.get("viewer_count", 0),
                    language=stream_data.get("language", "en"),
                    category=stream_data.get("game_name", ""),
                    metadata=stream_data,
                )

            else:
                return StepResult.fail(f"Unsupported platform: {platform}")

            return StepResult.ok(data={"stream_info": stream_info})

        except Exception as e:
            logger.error(f"Failed to get stream info: {e!s}")
            return StepResult.fail(f"Failed to get stream info: {e!s}")

    async def _analyze_sentiment(self, text: str) -> SentimentScore:
        """Analyze sentiment of text."""
        try:
            # Simple sentiment analysis based on keywords
            positive_keywords = [
                "good",
                "great",
                "awesome",
                "amazing",
                "love",
                "best",
                "excellent",
            ]
            negative_keywords = [
                "bad",
                "terrible",
                "awful",
                "hate",
                "worst",
                "horrible",
                "disgusting",
            ]

            text_lower = text.lower()
            positive_count = sum(1 for word in positive_keywords if word in text_lower)
            negative_count = sum(1 for word in negative_keywords if word in text_lower)

            # Calculate sentiment score
            if positive_count > negative_count:
                score = min(1.0, positive_count / 5.0)
                label = "positive"
            elif negative_count > positive_count:
                score = max(-1.0, -negative_count / 5.0)
                label = "negative"
            else:
                score = 0.0
                label = "neutral"

            confidence = abs(score)

            return SentimentScore(
                score=score,
                confidence=confidence,
                label=label,
                keywords=positive_keywords + negative_keywords,
            )

        except Exception as e:
            logger.error(f"Failed to analyze sentiment: {e!s}")
            return SentimentScore(score=0.0, confidence=0.0, label="neutral")

    def _extract_emotes(self, message: str) -> list[str]:
        """Extract emotes from a message."""
        try:
            # Simple emote extraction
            emotes = []

            # Common emotes
            common_emotes = [
                "😂",
                "🤣",
                "😆",
                "😄",
                "😃",
                "😀",
                "😊",
                "😍",
                "🥰",
                "😘",
                "😭",
                "😢",
                "😡",
                "😤",
                "🤔",
                "😏",
                "🙄",
                "😒",
                "😴",
                "🤤",
                "😋",
                "😎",
                "🤓",
                "😇",
                "🤗",
                "🤝",
                "👏",
                "👍",
                "👎",
                "❤️",
                "💔",
                "🔥",
                "💯",
                "⭐",
                "🌟",
                "✨",
                "💫",
                "🌈",
                "🎉",
                "🎊",
                "🎈",
                "🎁",
                "🎂",
                "🍰",
                "🍕",
                "🍔",
                "🍟",
                "🌭",
                "🌮",
                "🌯",
                "🥙",
                "🌮",
                "🌯",
                "🥙",
                "🌮",
                "🌯",
                "🥙",
            ]

            for emote in common_emotes:
                if emote in message:
                    emotes.append(emote)

            return emotes

        except Exception as e:
            logger.error(f"Failed to extract emotes: {e!s}")
            return []

    def _calculate_baseline_velocity(self, stream_key: str) -> float:
        """Calculate baseline chat velocity for a stream."""
        try:
            chat_queue = self.chat_queues[stream_key]

            if len(chat_queue) < 10:
                return 1.0  # Default baseline

            # Calculate average messages per minute over last 10 minutes
            now = datetime.now()
            ten_minutes_ago = now - timedelta(minutes=10)

            recent_messages = [msg for msg in chat_queue if msg.timestamp >= ten_minutes_ago]

            if len(recent_messages) < 5:
                return 1.0

            # Calculate velocity
            time_span = (now - ten_minutes_ago).total_seconds() / 60.0  # minutes
            velocity = len(recent_messages) / time_span

            return max(1.0, velocity)

        except Exception as e:
            logger.error(f"Failed to calculate baseline velocity: {e!s}")
            return 1.0

    async def get_monitoring_status(self) -> StepResult:
        """Get current monitoring status."""
        try:
            status = {
                "active_streams": len(self.active_streams),
                "monitoring_configs": len(self.monitoring_configs),
                "viral_moments_detected": len(self.viral_moments),
                "clip_candidates_generated": len(self.clip_candidates),
                "streams": list(self.active_streams.keys()),
                "recent_moments": [
                    {
                        "moment_id": moment.moment_id,
                        "type": moment.moment_type.value,
                        "timestamp": moment.timestamp.isoformat(),
                        "confidence": moment.confidence,
                        "description": moment.description,
                    }
                    for moment in self.viral_moments[-10:]  # Last 10 moments
                ],
            }

            return StepResult.ok(data={"status": status})

        except Exception as e:
            logger.error(f"Failed to get monitoring status: {e!s}")
            return StepResult.fail(f"Failed to get monitoring status: {e!s}")

    async def cleanup(self) -> None:
        """Cleanup resources."""
        try:
            # Stop all monitoring
            for stream_key in list(self.monitoring_tasks.keys()):
                await self.stop_monitoring(stream_key)

            # Clear data
            self.viral_moments.clear()
            self.clip_candidates.clear()
            self.chat_queues.clear()
            self.sentiment_history.clear()
            self.baseline_metrics.clear()
            self.moment_callbacks.clear()
            self.clip_callbacks.clear()

            logger.info("Live Clip Radar cleanup completed")

        except Exception as e:
            logger.error(f"Failed to cleanup Live Clip Radar: {e!s}")
