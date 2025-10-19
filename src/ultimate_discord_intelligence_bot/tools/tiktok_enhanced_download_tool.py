"""Enhanced TikTok downloader with creator tracking."""

from __future__ import annotations

import time
from datetime import datetime
from typing import Any, TypedDict

from ultimate_discord_intelligence_bot.step_result import StepResult
from ultimate_discord_intelligence_bot.tools._base import BaseTool


class TikTokVideo(TypedDict, total=False):
    """TikTok video data structure."""

    video_id: str
    creator_handle: str
    creator_name: str
    title: str
    description: str
    video_url: str
    thumbnail_url: str
    duration_seconds: int
    view_count: int
    like_count: int
    comment_count: int
    share_count: int
    timestamp: float
    hashtags: list[str]
    mentions: list[str]
    music_info: dict[str, Any] | None
    effects_used: list[str] | None


class TikTokProfile(TypedDict, total=False):
    """TikTok profile data structure."""

    handle: str
    name: str
    bio: str
    follower_count: int
    following_count: int
    video_count: int
    like_count: int
    verified: bool
    profile_picture_url: str
    last_updated: float


class TikTokDownloadResult(TypedDict, total=False):
    """Result of TikTok download operation."""

    mode: str
    input_identifier: str
    videos_found: int
    videos_downloaded: int
    videos_failed: int
    profile_data: TikTokProfile | None
    video_data: list[TikTokVideo]
    download_urls: list[str]
    processing_time_seconds: float
    errors: list[str]
    next_check_recommended: float | None


class TikTokEnhancedDownloadTool(BaseTool[StepResult]):
    """Enhanced TikTok downloader with creator tracking."""

    name: str = "TikTok Enhanced Download"
    description: str = (
        "Enhanced TikTok downloader with creator tracking. Supports single video download, "
        "profile monitoring, and real-time monitoring for new posts"
    )

    def __init__(self) -> None:
        super().__init__()
        self._downloaded_videos: set[str] = set()
        self._profile_cache: dict[str, TikTokProfile] = {}
        self._last_check_times: dict[str, float] = {}

    def _run(self, url_or_handle: str, mode: str, tenant: str, workspace: str) -> StepResult:
        """
        Download TikTok content based on mode.

        Args:
            url_or_handle: TikTok URL or creator handle
            mode: Download mode ("single", "profile", "monitor")
            tenant: Tenant identifier
            workspace: Workspace identifier

        Returns:
            StepResult with download results
        """
        try:
            if not url_or_handle or not mode:
                return StepResult.fail("URL/handle and mode are required")

            if mode not in ["single", "profile", "monitor"]:
                return StepResult.fail("Mode must be 'single', 'profile', or 'monitor'")

            start_time = time.time()

            if mode == "single":
                result = self._download_single_video(url_or_handle, tenant, workspace)
            elif mode == "profile":
                result = self._download_profile_videos(url_or_handle, tenant, workspace)
            elif mode == "monitor":
                result = self._monitor_profile(url_or_handle, tenant, workspace)
            else:
                return StepResult.fail(f"Unknown mode: {mode}")

            result["processing_time_seconds"] = time.time() - start_time

            return StepResult.ok(data=result)

        except Exception as e:
            return StepResult.fail(f"TikTok download failed: {str(e)}")

    def _download_single_video(self, video_url: str, tenant: str, workspace: str) -> TikTokDownloadResult:
        """Download a single TikTok video."""
        try:
            # Extract video ID from URL
            video_id = self._extract_video_id(video_url)

            if not video_id:
                return TikTokDownloadResult(
                    mode="single",
                    input_identifier=video_url,
                    videos_found=0,
                    videos_downloaded=0,
                    videos_failed=1,
                    profile_data=None,
                    video_data=[],
                    download_urls=[],
                    errors=["Could not extract video ID from URL"],
                )

            # Get video data
            video_data = self._get_video_data(video_id, tenant, workspace)

            if not video_data:
                return TikTokDownloadResult(
                    mode="single",
                    input_identifier=video_url,
                    videos_found=0,
                    videos_downloaded=0,
                    videos_failed=1,
                    profile_data=None,
                    video_data=[],
                    download_urls=[],
                    errors=["Could not retrieve video data"],
                )

            # Download video
            download_url = self._download_video_file(video_data, tenant, workspace)

            if download_url:
                self._downloaded_videos.add(video_id)
                return TikTokDownloadResult(
                    mode="single",
                    input_identifier=video_url,
                    videos_found=1,
                    videos_downloaded=1,
                    videos_failed=0,
                    profile_data=None,
                    video_data=[video_data],
                    download_urls=[download_url],
                    errors=[],
                )
            else:
                return TikTokDownloadResult(
                    mode="single",
                    input_identifier=video_url,
                    videos_found=1,
                    videos_downloaded=0,
                    videos_failed=1,
                    profile_data=None,
                    video_data=[video_data],
                    download_urls=[],
                    errors=["Failed to download video file"],
                )

        except Exception as e:
            return TikTokDownloadResult(
                mode="single",
                input_identifier=video_url,
                videos_found=0,
                videos_downloaded=0,
                videos_failed=1,
                profile_data=None,
                video_data=[],
                download_urls=[],
                errors=[str(e)],
            )

    def _download_profile_videos(self, handle: str, tenant: str, workspace: str) -> TikTokDownloadResult:
        """Download all videos from a TikTok profile."""
        try:
            # Get profile data
            profile_data = self._get_profile_data(handle, tenant, workspace)

            if not profile_data:
                return TikTokDownloadResult(
                    mode="profile",
                    input_identifier=handle,
                    videos_found=0,
                    videos_downloaded=0,
                    videos_failed=0,
                    profile_data=None,
                    video_data=[],
                    download_urls=[],
                    errors=[f"Could not retrieve profile data for {handle}"],
                )

            # Get all videos from profile
            videos = self._get_profile_videos(handle, tenant, workspace)

            downloaded_count = 0
            failed_count = 0
            download_urls: list[str] = []
            video_data_list: list[TikTokVideo] = []
            errors: list[str] = []

            for video in videos:
                try:
                    download_url = self._download_video_file(video, tenant, workspace)
                    if download_url:
                        downloaded_count += 1
                        download_urls.append(download_url)
                        self._downloaded_videos.add(video["video_id"])
                    else:
                        failed_count += 1
                        errors.append(f"Failed to download video {video['video_id']}")

                    video_data_list.append(video)

                except Exception as e:
                    failed_count += 1
                    errors.append(f"Error downloading video {video['video_id']}: {str(e)}")
                    video_data_list.append(video)

            return TikTokDownloadResult(
                mode="profile",
                input_identifier=handle,
                videos_found=len(videos),
                videos_downloaded=downloaded_count,
                videos_failed=failed_count,
                profile_data=profile_data,
                video_data=video_data_list,
                download_urls=download_urls,
                errors=errors,
            )

        except Exception as e:
            return TikTokDownloadResult(
                mode="profile",
                input_identifier=handle,
                videos_found=0,
                videos_downloaded=0,
                videos_failed=0,
                profile_data=None,
                video_data=[],
                download_urls=[],
                errors=[str(e)],
            )

    def _monitor_profile(self, handle: str, tenant: str, workspace: str) -> TikTokDownloadResult:
        """Monitor a profile for new videos."""
        try:
            # Get profile data
            profile_data = self._get_profile_data(handle, tenant, workspace)

            if not profile_data:
                return TikTokDownloadResult(
                    mode="monitor",
                    input_identifier=handle,
                    videos_found=0,
                    videos_downloaded=0,
                    videos_failed=0,
                    profile_data=None,
                    video_data=[],
                    download_urls=[],
                    errors=[f"Could not retrieve profile data for {handle}"],
                )

            # Get recent videos (last 24 hours)
            recent_videos = self._get_recent_videos(handle, tenant, workspace)

            # Filter for new videos (not already downloaded)
            new_videos = [video for video in recent_videos if video["video_id"] not in self._downloaded_videos]

            downloaded_count = 0
            failed_count = 0
            download_urls: list[str] = []
            video_data_list: list[TikTokVideo] = []
            errors: list[str] = []

            for video in new_videos:
                try:
                    download_url = self._download_video_file(video, tenant, workspace)
                    if download_url:
                        downloaded_count += 1
                        download_urls.append(download_url)
                        self._downloaded_videos.add(video["video_id"])
                    else:
                        failed_count += 1
                        errors.append(f"Failed to download video {video['video_id']}")

                    video_data_list.append(video)

                except Exception as e:
                    failed_count += 1
                    errors.append(f"Error downloading video {video['video_id']}: {str(e)}")
                    video_data_list.append(video)

            # Update last check time
            self._last_check_times[handle] = time.time()

            return TikTokDownloadResult(
                mode="monitor",
                input_identifier=handle,
                videos_found=len(new_videos),
                videos_downloaded=downloaded_count,
                videos_failed=failed_count,
                profile_data=profile_data,
                video_data=video_data_list,
                download_urls=download_urls,
                errors=errors,
                next_check_recommended=time.time() + (10 * 60),  # 10 minutes
            )

        except Exception as e:
            return TikTokDownloadResult(
                mode="monitor",
                input_identifier=handle,
                videos_found=0,
                videos_downloaded=0,
                videos_failed=0,
                profile_data=None,
                video_data=[],
                download_urls=[],
                errors=[str(e)],
            )

    def _extract_video_id(self, video_url: str) -> str | None:
        """Extract video ID from TikTok URL."""
        try:
            # Mock implementation - in real system, would parse TikTok URL patterns
            if "tiktok.com" in video_url:
                # Extract ID from URL pattern
                parts = video_url.split("/")
                if len(parts) >= 4:
                    return parts[-1].split("?")[0]  # Remove query parameters
            return None
        except Exception:
            return None

    def _get_video_data(self, video_id: str, tenant: str, workspace: str) -> TikTokVideo | None:
        """Get video data from TikTok API."""
        try:
            # Mock implementation - in real system, would use TikTok API
            current_time = time.time()

            return TikTokVideo(
                video_id=video_id,
                creator_handle="example_creator",
                creator_name="Example Creator",
                title="Example TikTok Video",
                description="This is an example TikTok video description with #hashtags and @mentions",
                video_url=f"https://tiktok.com/video/{video_id}",
                thumbnail_url=f"https://tiktok.com/thumbnail/{video_id}.jpg",
                duration_seconds=30,
                view_count=10000,
                like_count=500,
                comment_count=50,
                share_count=25,
                timestamp=current_time - 3600,  # 1 hour ago
                hashtags=["#example", "#tiktok", "#viral"],
                mentions=["@friend1", "@friend2"],
                music_info={"title": "Example Song", "artist": "Example Artist", "duration": 30},
                effects_used=["filter1", "transition1"],
            )
        except Exception:
            return None

    def _get_profile_data(self, handle: str, tenant: str, workspace: str) -> TikTokProfile | None:
        """Get TikTok profile data."""
        try:
            # Check cache first
            if handle in self._profile_cache:
                cached_profile = self._profile_cache[handle]
                # Return cached data if less than 1 hour old
                if time.time() - cached_profile["last_updated"] < 3600:
                    return cached_profile

            # Mock implementation - in real system, would use TikTok API
            current_time = time.time()

            profile = TikTokProfile(
                handle=handle,
                name="Example Creator Name",
                bio="This is an example TikTok creator bio",
                follower_count=100000,
                following_count=500,
                video_count=1000,
                like_count=5000000,
                verified=True,
                profile_picture_url=f"https://tiktok.com/profile/{handle}.jpg",
                last_updated=current_time,
            )

            # Cache the profile
            self._profile_cache[handle] = profile

            return profile

        except Exception:
            return None

    def _get_profile_videos(self, handle: str, tenant: str, workspace: str) -> list[TikTokVideo]:
        """Get all videos from a TikTok profile."""
        try:
            # Mock implementation - in real system, would use TikTok API
            videos: list[TikTokVideo] = []
            current_time = time.time()

            # Generate mock videos
            for i in range(10):  # Mock 10 videos
                video = TikTokVideo(
                    video_id=f"{handle}_video_{i}",
                    creator_handle=handle,
                    creator_name="Example Creator",
                    title=f"Example Video {i}",
                    description=f"This is example video {i} with #hashtags",
                    video_url=f"https://tiktok.com/video/{handle}_video_{i}",
                    thumbnail_url=f"https://tiktok.com/thumbnail/{handle}_video_{i}.jpg",
                    duration_seconds=30 + (i * 5),
                    view_count=1000 + (i * 100),
                    like_count=50 + (i * 10),
                    comment_count=5 + i,
                    share_count=2 + i,
                    timestamp=current_time - (i * 3600),  # Each video 1 hour older
                    hashtags=[f"#example{i}", "#tiktok"],
                    mentions=[],
                    music_info={"title": f"Example Song {i}", "artist": "Example Artist", "duration": 30 + (i * 5)},
                    effects_used=[f"filter{i}"],
                )
                videos.append(video)

            return videos

        except Exception:
            return []

    def _get_recent_videos(self, handle: str, tenant: str, workspace: str) -> list[TikTokVideo]:
        """Get recent videos from a TikTok profile (last 24 hours)."""
        try:
            all_videos = self._get_profile_videos(handle, tenant, workspace)
            current_time = time.time()
            day_ago = current_time - (24 * 3600)

            # Filter for videos from last 24 hours
            recent_videos = [video for video in all_videos if video["timestamp"] >= day_ago]

            return recent_videos

        except Exception:
            return []

    def _download_video_file(self, video: TikTokVideo, tenant: str, workspace: str) -> str | None:
        """Download video file and return archive URL."""
        try:
            # Mock implementation - in real system, would:
            # 1. Download video from TikTok URL
            # 2. Store in S3/MinIO or similar
            # 3. Return permanent archive URL

            video_id = video["video_id"]
            creator_handle = video["creator_handle"]

            # Generate archive filename
            timestamp = datetime.fromtimestamp(video["timestamp"]).strftime("%Y%m%d_%H%M%S")
            filename = f"{tenant}/{workspace}/tiktok/{creator_handle}_{timestamp}_{video_id}.mp4"

            # Mock archive URL
            archive_url = f"https://archive.example.com/{filename}"

            # In real implementation, would download and upload here
            print(f"Mock: Downloaded TikTok video {video_id} to {archive_url}")

            return archive_url

        except Exception as e:
            print(f"Error downloading video {video['video_id']}: {e}")
            return None

    def get_downloaded_count(self) -> int:
        """Get the total number of downloaded videos."""
        return len(self._downloaded_videos)

    def is_video_downloaded(self, video_id: str) -> bool:
        """Check if a video has already been downloaded."""
        return video_id in self._downloaded_videos

    def get_last_check_time(self, handle: str) -> float | None:
        """Get the last check time for a specific handle."""
        return self._last_check_times.get(handle)
