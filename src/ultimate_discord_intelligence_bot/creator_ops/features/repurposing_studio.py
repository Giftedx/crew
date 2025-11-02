"""
Repurposing Studio for converting long-form content into platform-specific shorts.
Handles video processing, clip generation, and platform optimization.
"""

import asyncio
import logging
import tempfile
from datetime import datetime
from pathlib import Path
from platform.core.step_result import StepResult

from ultimate_discord_intelligence_bot.creator_ops.config import CreatorOpsConfig
from ultimate_discord_intelligence_bot.creator_ops.features.repurposing_models import (
    CaptionStyle,
    ClipCandidate,
    ClipStatus,
    FFmpegConfig,
    PlatformHook,
    PlatformType,
    RepurposingConfig,
    RepurposingJob,
    RepurposingResult,
    VideoClip,
)
from ultimate_discord_intelligence_bot.creator_ops.knowledge.api import KnowledgeAPI
from ultimate_discord_intelligence_bot.creator_ops.media import NLPPipeline
from ultimate_discord_intelligence_bot.creator_ops.media.alignment import AlignedTranscript, TranscriptAlignment


logger = logging.getLogger(__name__)


class RepurposingStudio:
    """Main class for repurposing long-form content into platform-specific shorts."""

    def __init__(self, config: CreatorOpsConfig, knowledge_api: KnowledgeAPI):
        self.config = config
        self.knowledge_api = knowledge_api
        self.alignment = TranscriptAlignment(config)
        self.nlp_pipeline = NLPPipeline(config)
        self.temp_dir = Path(tempfile.gettempdir()) / "repurposing_studio"
        self.temp_dir.mkdir(exist_ok=True)

    async def repurpose_episode(
        self,
        episode_id: str,
        video_file_path: str,
        transcript: AlignedTranscript,
        target_platforms: list[PlatformType],
        repurposing_config: RepurposingConfig | None = None,
    ) -> StepResult:
        """
        Repurpose an episode into platform-specific shorts.

        Args:
            episode_id: Unique identifier for the episode
            video_file_path: Path to the source video file
            transcript: Aligned transcript with speaker diarization
            target_platforms: List of platforms to target
            repurposing_config: Configuration for repurposing process

        Returns:
            StepResult with repurposing job details
        """
        try:
            if not repurposing_config:
                repurposing_config = RepurposingConfig()
            job = RepurposingJob(
                job_id=f"repurpose_{episode_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                episode_id=episode_id,
                episode_title=transcript.metadata.get("title", "Untitled Episode"),
                episode_duration=transcript.duration,
                target_platforms=target_platforms,
                clip_count=repurposing_config.target_clip_count,
                status=ClipStatus.PENDING,
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )
            logger.info(f"Starting repurposing job {job.job_id} for episode {episode_id}")
            candidates_result = await self._identify_clip_candidates(transcript, repurposing_config)
            if not candidates_result.success:
                return StepResult.fail(f"Failed to identify clip candidates: {candidates_result.error}")
            candidates = candidates_result.data["candidates"]
            logger.info(f"Identified {len(candidates)} clip candidates")
            clips = []
            for i, candidate in enumerate(candidates[: repurposing_config.target_clip_count]):
                clip_result = await self._generate_clip(job, candidate, video_file_path, repurposing_config)
                if clip_result.success:
                    clips.append(clip_result.data["clip"])
                else:
                    logger.warning(f"Failed to generate clip {i + 1}: {clip_result.error}")
            job.clips = clips
            job.status = ClipStatus.COMPLETED if clips else ClipStatus.FAILED
            job.updated_at = datetime.now()
            if repurposing_config.auto_generate_hooks:
                hooks_result = await self._generate_platform_hooks(job, transcript)
                if hooks_result.success:
                    job.hooks = hooks_result.data["hooks"]
            result = RepurposingResult(
                job_id=job.job_id,
                success=len(clips) > 0,
                clips_created=len(clips),
                total_duration=sum(clip.duration for clip in clips),
                platforms_targeted=target_platforms,
                output_files=[clip.file_path for clip in clips],
                metadata={
                    "episode_id": episode_id,
                    "episode_title": job.episode_title,
                    "episode_duration": job.episode_duration,
                    "clip_candidates_found": len(candidates),
                    "clips_generated": len(clips),
                    "platforms_targeted": [p.value for p in target_platforms],
                },
            )
            logger.info(f"Repurposing job {job.job_id} completed: {len(clips)} clips created")
            return StepResult.ok(data={"job": job, "result": result})
        except Exception as e:
            logger.error(f"Repurposing job failed: {e!s}")
            return StepResult.fail(f"Repurposing job failed: {e!s}")

    async def _identify_clip_candidates(self, transcript: AlignedTranscript, config: RepurposingConfig) -> StepResult:
        """Identify candidate segments for clip creation."""
        try:
            candidates = []
            for segment in transcript.segments:
                if not self._is_valid_clip_segment(segment, config):
                    continue
                engagement_score = self._calculate_engagement_score(segment, transcript)
                viral_potential = self._calculate_viral_potential(segment, transcript)
                reason = self._generate_selection_reason(segment, engagement_score, viral_potential)
                candidate = ClipCandidate(
                    start_time=segment.start_time,
                    end_time=segment.end_time,
                    duration=segment.end_time - segment.start_time,
                    transcript_segment=segment.text,
                    speakers=segment.speakers,
                    topics=segment.topics or [],
                    sentiment_score=segment.sentiment_score or 0.0,
                    engagement_score=engagement_score,
                    viral_potential=viral_potential,
                    reason=reason,
                )
                candidates.append(candidate)
            candidates.sort(key=lambda c: c.engagement_score + c.viral_potential, reverse=True)
            return StepResult.ok(data={"candidates": candidates})
        except Exception as e:
            logger.error(f"Failed to identify clip candidates: {e!s}")
            return StepResult.fail(f"Failed to identify clip candidates: {e!s}")

    def _is_valid_clip_segment(self, segment, config: RepurposingConfig) -> bool:
        """Check if a segment is valid for clip creation."""
        duration = segment.end_time - segment.start_time
        if duration < config.min_clip_duration or duration > config.max_clip_duration:
            return False
        if len(segment.text.strip()) < 50:
            return False
        if len(segment.speakers) > 1:
            return True
        engaging_words = ["amazing", "incredible", "unbelievable", "shocking", "controversial", "breaking"]
        if any(word in segment.text.lower() for word in engaging_words):
            return True
        return True

    def _calculate_engagement_score(self, segment, transcript: AlignedTranscript) -> float:
        """Calculate engagement score for a segment."""
        score = 0.0
        if segment.sentiment_score:
            score += abs(segment.sentiment_score) * 0.3
        if len(segment.speakers) > 1:
            score += 0.2
        if "?" in segment.text:
            score += 0.1
        if "!" in segment.text:
            score += 0.1
        if any(char.isdigit() for char in segment.text):
            score += 0.1
        if segment.topics and len(segment.topics) > 0:
            score += 0.1
        return min(score, 1.0)

    def _calculate_viral_potential(self, segment, transcript: AlignedTranscript) -> float:
        """Calculate viral potential for a segment."""
        score = 0.0
        controversial_topics = ["politics", "religion", "controversy", "scandal", "breaking news"]
        if segment.topics:
            for topic in segment.topics:
                if any(controversial in topic.lower() for controversial in controversial_topics):
                    score += 0.3
                    break
        emotional_words = ["love", "hate", "angry", "excited", "shocked", "amazed"]
        if any(word in segment.text.lower() for word in emotional_words):
            score += 0.2
        trending_keywords = ["viral", "trending", "popular", "famous", "celebrity"]
        if any(keyword in segment.text.lower() for keyword in trending_keywords):
            score += 0.2
        cta_phrases = ["share", "subscribe", "like", "comment", "follow"]
        if any(phrase in segment.text.lower() for phrase in cta_phrases):
            score += 0.1
        return min(score, 1.0)

    def _generate_selection_reason(self, segment, engagement_score: float, viral_potential: float) -> str:
        """Generate a reason for why this segment was selected."""
        reasons = []
        if engagement_score > 0.7:
            reasons.append("high engagement potential")
        if viral_potential > 0.7:
            reasons.append("high viral potential")
        if len(segment.speakers) > 1:
            reasons.append("multiple speakers")
        if "?" in segment.text:
            reasons.append("contains questions")
        if segment.topics and len(segment.topics) > 0:
            reasons.append(f"covers topics: {', '.join(segment.topics[:3])}")
        if not reasons:
            reasons.append("meaningful content")
        return f"Selected because: {', '.join(reasons)}"

    async def _generate_clip(
        self, job: RepurposingJob, candidate: ClipCandidate, video_file_path: str, config: RepurposingConfig
    ) -> StepResult:
        """Generate a video clip from a candidate segment."""
        try:
            clip_dir = self.temp_dir / job.job_id / f"clip_{len(job.clips) + 1}"
            clip_dir.mkdir(parents=True, exist_ok=True)
            clips = []
            for platform in job.target_platforms:
                aspect_ratio = config.aspect_ratios[platform]
                resolution = config.resolutions[platform]
                clip_id = f"{job.job_id}_clip_{len(job.clips) + 1}_{platform.value}"
                ffmpeg_config = FFmpegConfig(
                    input_file=video_file_path,
                    output_file=str(clip_dir / f"{clip_id}.mp4"),
                    start_time=candidate.start_time,
                    end_time=candidate.end_time,
                    aspect_ratio=aspect_ratio,
                    resolution=resolution,
                    metadata={
                        "title": candidate.transcript_segment[:100],
                        "description": candidate.transcript_segment,
                        "platform": platform.value,
                    },
                )
                clip_result = await self._process_video_with_ffmpeg(ffmpeg_config, config)
                if not clip_result.success:
                    logger.warning(f"Failed to process video for {platform}: {clip_result.error}")
                    continue
                captions_path = None
                if config.caption_style:
                    captions_result = await self._generate_captions(candidate, clip_dir, clip_id, config.caption_style)
                    if captions_result.success:
                        captions_path = captions_result.data["captions_path"]
                clip = VideoClip(
                    clip_id=clip_id,
                    episode_id=job.episode_id,
                    title=candidate.transcript_segment[:100],
                    description=candidate.transcript_segment,
                    start_time=candidate.start_time,
                    end_time=candidate.end_time,
                    duration=candidate.duration,
                    aspect_ratio=aspect_ratio,
                    resolution=resolution,
                    file_path=ffmpeg_config.output_file,
                    thumbnail_path=str(clip_dir / f"{clip_id}_thumb.jpg"),
                    captions_path=captions_path,
                    status=ClipStatus.COMPLETED,
                    created_at=datetime.now(),
                    updated_at=datetime.now(),
                    metadata={
                        "platform": platform.value,
                        "engagement_score": candidate.engagement_score,
                        "viral_potential": candidate.viral_potential,
                        "speakers": candidate.speakers,
                        "topics": candidate.topics,
                        "selection_reason": candidate.reason,
                    },
                )
                clips.append(clip)
            return StepResult.ok(data={"clips": clips})
        except Exception as e:
            logger.error(f"Failed to generate clip: {e!s}")
            return StepResult.fail(f"Failed to generate clip: {e!s}")

    async def _process_video_with_ffmpeg(self, ffmpeg_config: FFmpegConfig, config: RepurposingConfig) -> StepResult:
        """Process video using FFmpeg."""
        try:
            cmd = [
                "ffmpeg",
                "-i",
                ffmpeg_config.input_file,
                "-ss",
                str(ffmpeg_config.start_time),
                "-t",
                str(ffmpeg_config.end_time - ffmpeg_config.start_time),
                "-vf",
                f"scale={ffmpeg_config.resolution.split('x')[0]}:{ffmpeg_config.resolution.split('x')[1]}",
                "-c:v",
                "libx264",
                "-b:v",
                ffmpeg_config.bitrate,
                "-c:a",
                "aac",
                "-b:a",
                ffmpeg_config.audio_bitrate,
                "-r",
                str(ffmpeg_config.fps),
                "-y",
                ffmpeg_config.output_file,
            ]
            for key, value in ffmpeg_config.metadata.items():
                cmd.extend(["-metadata", f"{key}={value}"])
            process = await asyncio.create_subprocess_exec(
                *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
            )
            _stdout, stderr = await process.communicate()
            if process.returncode != 0:
                error_msg = stderr.decode() if stderr else "Unknown FFmpeg error"
                return StepResult.fail(f"FFmpeg processing failed: {error_msg}")
            thumbnail_cmd = [
                "ffmpeg",
                "-i",
                ffmpeg_config.output_file,
                "-ss",
                "00:00:01",
                "-vframes",
                "1",
                "-y",
                ffmpeg_config.output_file.replace(".mp4", "_thumb.jpg"),
            ]
            thumbnail_process = await asyncio.create_subprocess_exec(
                *thumbnail_cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
            )
            await thumbnail_process.communicate()
            return StepResult.ok(data={"output_file": ffmpeg_config.output_file})
        except Exception as e:
            logger.error(f"FFmpeg processing failed: {e!s}")
            return StepResult.fail(f"FFmpeg processing failed: {e!s}")

    async def _generate_captions(
        self, candidate: ClipCandidate, clip_dir: Path, clip_id: str, caption_style: CaptionStyle
    ) -> StepResult:
        """Generate captions for a clip."""
        try:
            srt_path = clip_dir / f"{clip_id}.srt"
            with open(srt_path, "w") as f:
                f.write("1\n")
                f.write("00:00:00,000 --> 00:00:05,000\n")
                f.write(candidate.transcript_segment)
                f.write("\n\n")
            vtt_path = clip_dir / f"{clip_id}.vtt"
            with open(vtt_path, "w") as f:
                f.write("WEBVTT\n\n")
                f.write("00:00:00.000 --> 00:00:05.000\n")
                f.write(candidate.transcript_segment)
                f.write("\n\n")
            return StepResult.ok(data={"captions_path": str(srt_path)})
        except Exception as e:
            logger.error(f"Failed to generate captions: {e!s}")
            return StepResult.fail(f"Failed to generate captions: {e!s}")

    async def _generate_platform_hooks(self, job: RepurposingJob, transcript: AlignedTranscript) -> StepResult:
        """Generate platform-specific hooks for clips."""
        try:
            hooks = []
            for platform in job.target_platforms:
                hook_text = self._generate_hook_text(platform, transcript)
                hashtags = self._generate_hashtags(platform, transcript)
                call_to_action = self._generate_call_to_action(platform)
                hook = PlatformHook(
                    platform=platform,
                    hook_text=hook_text,
                    hashtags=hashtags,
                    mentions=[],
                    call_to_action=call_to_action,
                    trending_topics=[],
                    engagement_tips=self._get_engagement_tips(platform),
                )
                hooks.append(hook)
            return StepResult.ok(data={"hooks": hooks})
        except Exception as e:
            logger.error(f"Failed to generate platform hooks: {e!s}")
            return StepResult.fail(f"Failed to generate platform hooks: {e!s}")

    def _generate_hook_text(self, platform: PlatformType, transcript: AlignedTranscript) -> str:
        """Generate hook text for a specific platform."""
        if platform == PlatformType.YOUTUBE_SHORTS:
            return f"🎥 {transcript.metadata.get('title', 'Epic Moment')} - Full episode in bio! #shorts"
        elif platform == PlatformType.TIKTOK:
            return f"🔥 {transcript.metadata.get('title', 'This will blow your mind')} #fyp #viral"
        elif platform == PlatformType.INSTAGRAM_REELS:
            return f"✨ {transcript.metadata.get('title', 'Must see moment')} - Link in bio! #reels"
        elif platform == PlatformType.X:
            return f"🚀 {transcript.metadata.get('title', 'Breaking: Epic moment')} - Full thread below 👇"
        else:
            return f"🎬 {transcript.metadata.get('title', 'Amazing moment')}"

    def _generate_hashtags(self, platform: PlatformType, transcript: AlignedTranscript) -> list[str]:
        """Generate hashtags for a specific platform."""
        base_hashtags = []
        if platform == PlatformType.YOUTUBE_SHORTS:
            base_hashtags = ["#shorts", "#youtube", "#viral"]
        elif platform == PlatformType.TIKTOK:
            base_hashtags = ["#fyp", "#viral", "#tiktok", "#trending"]
        elif platform == PlatformType.INSTAGRAM_REELS:
            base_hashtags = ["#reels", "#instagram", "#viral", "#trending"]
        elif platform == PlatformType.X:
            base_hashtags = ["#viral", "#trending", "#breaking"]
        if transcript.segments:
            for segment in transcript.segments[:5]:
                if segment.topics:
                    for topic in segment.topics[:3]:
                        hashtag = f"#{topic.replace(' ', '').lower()}"
                        if len(hashtag) <= 20:
                            base_hashtags.append(hashtag)
        return base_hashtags[:10]

    def _generate_call_to_action(self, platform: PlatformType) -> str:
        """Generate call-to-action for a specific platform."""
        if platform == PlatformType.YOUTUBE_SHORTS:
            return "Subscribe for more epic moments! 🔔"
        elif platform == PlatformType.TIKTOK:
            return "Follow for daily viral content! 👆"
        elif platform == PlatformType.INSTAGRAM_REELS:
            return "Follow for more amazing content! ✨"
        elif platform == PlatformType.X:
            return "Follow for more breaking updates! 🚀"
        else:
            return "Follow for more content!"

    def _get_engagement_tips(self, platform: PlatformType) -> list[str]:
        """Get engagement tips for a specific platform."""
        if platform == PlatformType.YOUTUBE_SHORTS:
            return [
                "Post during peak hours (6-9 PM)",
                "Use trending audio",
                "Keep it under 60 seconds",
                "Add captions for accessibility",
            ]
        elif platform == PlatformType.TIKTOK:
            return [
                "Post during peak hours (6-9 PM)",
                "Use trending hashtags",
                "Keep it under 60 seconds",
                "Add captions for accessibility",
            ]
        elif platform == PlatformType.INSTAGRAM_REELS:
            return [
                "Post during peak hours (6-9 PM)",
                "Use trending audio",
                "Keep it under 90 seconds",
                "Add captions for accessibility",
            ]
        elif platform == PlatformType.X:
            return [
                "Post during peak hours (9-11 AM, 1-3 PM)",
                "Use trending hashtags",
                "Keep it concise",
                "Add images/videos for engagement",
            ]
        else:
            return ["Post during peak hours", "Use trending content", "Engage with comments"]

    async def cleanup(self):
        """Clean up temporary files and resources."""
        try:
            if self.temp_dir.exists():
                import shutil

                shutil.rmtree(self.temp_dir)
            logger.info("Repurposing Studio cleanup completed")
        except Exception as e:
            logger.error(f"Failed to cleanup Repurposing Studio: {e!s}")
