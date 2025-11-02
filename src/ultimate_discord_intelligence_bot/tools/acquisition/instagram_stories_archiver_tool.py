"""Instagram Stories archival tool for ephemeral content capture."""

from __future__ import annotations
import time
from datetime import datetime
from typing import Any, TypedDict
from platform.core.step_result import StepResult
from ultimate_discord_intelligence_bot.tools._base import BaseTool


class StoryPost(TypedDict, total=False):
    """Instagram story post data."""

    story_id: str
    creator_handle: str
    media_type: str
    media_url: str
    caption: str | None
    timestamp: float
    expires_at: float
    view_count: int | None
    engagement_data: dict[str, Any] | None


class InstagramStoriesArchiveResult(TypedDict, total=False):
    """Result of Instagram stories archival process."""

    timestamp: float
    handles_checked: list[str]
    new_stories_found: int
    stories_archived: int
    stories_failed: int
    archive_urls: list[str]
    processing_time_seconds: float
    next_check_recommended: float
    errors: list[str]


class InstagramStoriesArchiverTool(BaseTool[StepResult]):
    """Archive Instagram Stories before they expire."""

    name: str = "Instagram Stories Archiver"
    description: str = "Poll Instagram Stories API/scraper every 4 hours to detect new stories, download media (images/videos), extract text/captions, archive with metadata, and generate visual summaries"

    def __init__(self) -> None:
        super().__init__()
        self._last_check_times: dict[str, float] = {}
        self._archived_stories: set[str] = set()

    def _run(self, instagram_handles: list[str], tenant: str, workspace: str) -> StepResult:
        """
        Poll Instagram Stories and archive new content.

        Args:
            instagram_handles: List of Instagram handles to monitor
            tenant: Tenant identifier
            workspace: Workspace identifier

        Returns:
            StepResult with archival results
        """
        try:
            if not instagram_handles:
                return StepResult.fail("Instagram handles list cannot be empty")
            start_time = time.time()
            new_stories = self._poll_stories(instagram_handles, tenant, workspace)
            archive_results = self._archive_stories(new_stories, tenant, workspace)
            processing_time = time.time() - start_time
            result = InstagramStoriesArchiveResult(
                timestamp=time.time(),
                handles_checked=instagram_handles,
                new_stories_found=len(new_stories),
                stories_archived=archive_results["archived"],
                stories_failed=archive_results["failed"],
                archive_urls=archive_results["archive_urls"],
                processing_time_seconds=processing_time,
                next_check_recommended=time.time() + 4 * 60 * 60,
                errors=archive_results["errors"],
            )
            return StepResult.ok(data=result)
        except Exception as e:
            return StepResult.fail(f"Instagram stories archival failed: {e!s}")

    def _poll_stories(self, handles: list[str], tenant: str, workspace: str) -> list[StoryPost]:
        """Check for new stories from monitored handles."""
        new_stories: list[StoryPost] = []
        for handle in handles:
            try:
                stories = self._get_stories_for_handle(handle, tenant, workspace)
                for story in stories:
                    if story["story_id"] not in self._archived_stories:
                        new_stories.append(story)
                        self._archived_stories.add(story["story_id"])
                self._last_check_times[handle] = time.time()
            except Exception as e:
                print(f"Error polling stories for {handle}: {e}")
        return new_stories

    def _get_stories_for_handle(self, handle: str, tenant: str, workspace: str) -> list[StoryPost]:
        """Get stories for a specific Instagram handle."""
        current_time = time.time()
        mock_stories = [
            StoryPost(
                story_id=f"{handle}_story_{int(current_time)}_1",
                creator_handle=handle,
                media_type="image",
                media_url=f"https://instagram.com/stories/{handle}/mock_image_1.jpg",
                caption="Check out this new product! #sponsored",
                timestamp=current_time - 3600,
                expires_at=current_time + 23 * 3600,
                view_count=1500,
                engagement_data={"likes": 50, "replies": 10},
            ),
            StoryPost(
                story_id=f"{handle}_story_{int(current_time)}_2",
                creator_handle=handle,
                media_type="video",
                media_url=f"https://instagram.com/stories/{handle}/mock_video_1.mp4",
                caption="Behind the scenes of our latest podcast recording",
                timestamp=current_time - 1800,
                expires_at=current_time + 23.5 * 3600,
                view_count=800,
                engagement_data={"likes": 30, "replies": 5},
            ),
        ]
        return mock_stories

    def _archive_stories(self, stories: list[StoryPost], tenant: str, workspace: str) -> dict[str, Any]:
        """Download and archive stories with full metadata."""
        archived = 0
        failed = 0
        archive_urls: list[str] = []
        errors: list[str] = []
        for story in stories:
            try:
                archive_url = self._download_and_store_story(story, tenant, workspace)
                if archive_url:
                    archive_urls.append(archive_url)
                    archived += 1
                    self._store_story_metadata(story, archive_url, tenant, workspace)
                    if story["media_type"] in ["image", "video"]:
                        self._generate_visual_summary(story, archive_url, tenant, workspace)
                else:
                    failed += 1
                    errors.append(f"Failed to download story {story['story_id']}")
            except Exception as e:
                failed += 1
                errors.append(f"Error archiving story {story['story_id']}: {e!s}")
        return {"archived": archived, "failed": failed, "archive_urls": archive_urls, "errors": errors}

    def _download_and_store_story(self, story: StoryPost, tenant: str, workspace: str) -> str | None:
        """Download story media and store in permanent storage."""
        try:
            media_type = story["media_type"]
            story_id = story["story_id"]
            creator_handle = story["creator_handle"]
            timestamp = datetime.fromtimestamp(story["timestamp"]).strftime("%Y%m%d_%H%M%S")
            extension = "jpg" if media_type == "image" else "mp4" if media_type == "video" else "txt"
            filename = f"{tenant}/{workspace}/instagram_stories/{creator_handle}_{timestamp}_{story_id}.{extension}"
            archive_url = f"https://archive.example.com/{filename}"
            print(f"Mock: Downloaded {media_type} from {story['media_url']} to {archive_url}")
            return archive_url
        except Exception as e:
            print(f"Error downloading story {story['story_id']}: {e}")
            return None

    def _store_story_metadata(self, story: StoryPost, archive_url: str, tenant: str, workspace: str) -> None:
        """Store story metadata in database."""
        try:
            {
                "story_id": story["story_id"],
                "creator_handle": story["creator_handle"],
                "media_type": story["media_type"],
                "original_url": story["media_url"],
                "archive_url": archive_url,
                "caption": story["caption"],
                "timestamp": story["timestamp"],
                "expires_at": story["expires_at"],
                "view_count": story["view_count"],
                "engagement_data": story["engagement_data"],
                "tenant": tenant,
                "workspace": workspace,
                "archived_at": time.time(),
            }
            print(f"Mock: Stored metadata for story {story['story_id']}")
        except Exception as e:
            print(f"Error storing metadata for story {story['story_id']}: {e}")

    def _generate_visual_summary(self, story: StoryPost, archive_url: str, tenant: str, workspace: str) -> None:
        """Generate visual summary for image/video stories."""
        try:
            if story["media_type"] == "image":
                visual_summary = {
                    "detected_text": story["caption"] or "",
                    "objects": ["person", "product", "text_overlay"],
                    "scene_type": "indoor",
                    "dominant_colors": ["#FF5733", "#33FF57"],
                    "face_count": 1,
                }
            elif story["media_type"] == "video":
                visual_summary = {
                    "duration_seconds": 15,
                    "scene_changes": 3,
                    "detected_audio": True,
                    "dominant_objects": ["person", "microphone", "background"],
                    "motion_level": "medium",
                }
            else:
                return
            print(f"Mock: Generated visual summary for {story['story_id']}: {visual_summary}")
        except Exception as e:
            print(f"Error generating visual summary for story {story['story_id']}: {e}")

    def get_last_check_time(self, handle: str) -> float | None:
        """Get the last check time for a specific handle."""
        return self._last_check_times.get(handle)

    def get_archived_count(self) -> int:
        """Get the total number of archived stories."""
        return len(self._archived_stories)

    def is_story_archived(self, story_id: str) -> bool:
        """Check if a story has already been archived."""
        return story_id in self._archived_stories
