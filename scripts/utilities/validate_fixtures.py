#!/usr/bin/env python3
"""
Fixture validation script for testing platform API fixtures.
Validates that all fixture files exist and contain valid data.
"""

import json
import logging
import sys
from pathlib import Path

from pydantic import ValidationError

# Add the project root to the path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

from ultimate_discord_intelligence_bot.creator_ops.integrations.instagram_models import (
    InstagramComment,
    InstagramInsight,
    InstagramMedia,
    InstagramStory,
    InstagramUser,
)
from ultimate_discord_intelligence_bot.creator_ops.integrations.tiktok_models import (
    TikTokComment,
    TikTokInsight,
    TikTokUser,
    TikTokVideo,
)
from ultimate_discord_intelligence_bot.creator_ops.integrations.twitch_models import (
    TwitchChatMessage,
    TwitchClip,
    TwitchEventSubSubscription,
    TwitchStream,
    TwitchUser,
    TwitchVideo,
)
from ultimate_discord_intelligence_bot.creator_ops.integrations.x_models import XMedia, XTweet, XUser
from ultimate_discord_intelligence_bot.creator_ops.integrations.youtube_models import (
    YouTubeCaption,
    YouTubeChannel,
    YouTubeCommentThread,
    YouTubeLiveChatMessage,
    YouTubeSearchResult,
    YouTubeVideo,
)

logger = logging.getLogger(__name__)


class FixtureValidator:
    """Validates fixture files for platform APIs."""

    def __init__(self):
        self.fixtures_dir = project_root / "fixtures" / "creator_ops"
        self.results: dict[str, dict] = {}
        self.errors: list[str] = []

    def validate_youtube_fixtures(self) -> dict:
        """Validate YouTube fixture files."""
        logger.info("Validating YouTube fixtures")

        youtube_fixtures = {
            "channels": "youtube_channels.json",
            "videos": "youtube_videos.json",
            "search": "youtube_search.json",
            "comments": "youtube_commentThreads.json",
            "captions": "youtube_captions.json",
            "live_chat": "youtube_liveChat_messages.json",
        }

        results = {}

        for fixture_name, filename in youtube_fixtures.items():
            try:
                file_path = self.fixtures_dir / filename
                if not file_path.exists():
                    self.errors.append(f"YouTube fixture {filename} not found")
                    results[fixture_name] = {"status": "missing", "error": "File not found"}
                    continue

                with open(file_path) as f:
                    data = json.load(f)

                # Validate based on fixture type
                if fixture_name == "channels":
                    if "items" in data:
                        for item in data["items"]:
                            YouTubeChannel(**item)
                    else:
                        YouTubeChannel(**data)
                elif fixture_name == "videos":
                    if "items" in data:
                        for item in data["items"]:
                            YouTubeVideo(**item)
                    else:
                        YouTubeVideo(**data)
                elif fixture_name == "search":
                    if "items" in data:
                        for item in data["items"]:
                            YouTubeSearchResult(**item)
                    else:
                        YouTubeSearchResult(**data)
                elif fixture_name == "comments":
                    if "items" in data:
                        for item in data["items"]:
                            YouTubeCommentThread(**item)
                    else:
                        YouTubeCommentThread(**data)
                elif fixture_name == "captions":
                    if "items" in data:
                        for item in data["items"]:
                            YouTubeCaption(**item)
                    else:
                        YouTubeCaption(**data)
                elif fixture_name == "live_chat":
                    if "items" in data:
                        for item in data["items"]:
                            YouTubeLiveChatMessage(**item)
                    else:
                        YouTubeLiveChatMessage(**data)

                results[fixture_name] = {
                    "status": "valid",
                    "file_size": file_path.stat().st_size,
                    "items_count": len(data.get("items", [data])),
                }

            except (json.JSONDecodeError, ValidationError) as e:
                self.errors.append(f"YouTube fixture {filename} validation error: {str(e)}")
                results[fixture_name] = {"status": "invalid", "error": str(e)}
            except Exception as e:
                self.errors.append(f"YouTube fixture {filename} unexpected error: {str(e)}")
                results[fixture_name] = {"status": "error", "error": str(e)}

        return results

    def validate_twitch_fixtures(self) -> dict:
        """Validate Twitch fixture files."""
        logger.info("Validating Twitch fixtures")

        twitch_fixtures = {
            "users": "twitch_users.json",
            "streams": "twitch_streams.json",
            "videos": "twitch_videos.json",
            "clips": "twitch_clips.json",
            "chat": "twitch_chat_messages.json",
            "eventsub": "twitch_eventsub_subscriptions.json",
        }

        results = {}

        for fixture_name, filename in twitch_fixtures.items():
            try:
                file_path = self.fixtures_dir / filename
                if not file_path.exists():
                    self.errors.append(f"Twitch fixture {filename} not found")
                    results[fixture_name] = {"status": "missing", "error": "File not found"}
                    continue

                with open(file_path) as f:
                    data = json.load(f)

                # Validate based on fixture type
                if fixture_name == "users":
                    if "data" in data:
                        for item in data["data"]:
                            TwitchUser(**item)
                    else:
                        TwitchUser(**data)
                elif fixture_name == "streams":
                    if "data" in data:
                        for item in data["data"]:
                            TwitchStream(**item)
                    else:
                        TwitchStream(**data)
                elif fixture_name == "videos":
                    if "data" in data:
                        for item in data["data"]:
                            TwitchVideo(**item)
                    else:
                        TwitchVideo(**data)
                elif fixture_name == "clips":
                    if "data" in data:
                        for item in data["data"]:
                            TwitchClip(**item)
                    else:
                        TwitchClip(**data)
                elif fixture_name == "chat":
                    if "data" in data:
                        for item in data["data"]:
                            TwitchChatMessage(**item)
                    else:
                        TwitchChatMessage(**data)
                elif fixture_name == "eventsub":
                    if "data" in data:
                        for item in data["data"]:
                            TwitchEventSubSubscription(**item)
                    else:
                        TwitchEventSubSubscription(**data)

                results[fixture_name] = {
                    "status": "valid",
                    "file_size": file_path.stat().st_size,
                    "items_count": len(data.get("data", [data])),
                }

            except (json.JSONDecodeError, ValidationError) as e:
                self.errors.append(f"Twitch fixture {filename} validation error: {str(e)}")
                results[fixture_name] = {"status": "invalid", "error": str(e)}
            except Exception as e:
                self.errors.append(f"Twitch fixture {filename} unexpected error: {str(e)}")
                results[fixture_name] = {"status": "error", "error": str(e)}

        return results

    def validate_tiktok_fixtures(self) -> dict:
        """Validate TikTok fixture files."""
        logger.info("Validating TikTok fixtures")

        tiktok_fixtures = {
            "user": "tiktok_user.json",
            "videos": "tiktok_videos.json",
            "comments": "tiktok_comments.json",
            "insights": "tiktok_insights.json",
        }

        results = {}

        for fixture_name, filename in tiktok_fixtures.items():
            try:
                file_path = self.fixtures_dir / filename
                if not file_path.exists():
                    self.errors.append(f"TikTok fixture {filename} not found")
                    results[fixture_name] = {"status": "missing", "error": "File not found"}
                    continue

                with open(file_path) as f:
                    data = json.load(f)

                # Validate based on fixture type
                if fixture_name == "user":
                    TikTokUser(**data)
                elif fixture_name == "videos":
                    if "data" in data:
                        for item in data["data"]:
                            TikTokVideo(**item)
                    else:
                        TikTokVideo(**data)
                elif fixture_name == "comments":
                    if "data" in data:
                        for item in data["data"]:
                            TikTokComment(**item)
                    else:
                        TikTokComment(**data)
                elif fixture_name == "insights":
                    if "data" in data:
                        for item in data["data"]:
                            TikTokInsight(**item)
                    else:
                        TikTokInsight(**data)

                results[fixture_name] = {
                    "status": "valid",
                    "file_size": file_path.stat().st_size,
                    "items_count": len(data.get("data", [data])),
                }

            except (json.JSONDecodeError, ValidationError) as e:
                self.errors.append(f"TikTok fixture {filename} validation error: {str(e)}")
                results[fixture_name] = {"status": "invalid", "error": str(e)}
            except Exception as e:
                self.errors.append(f"TikTok fixture {filename} unexpected error: {str(e)}")
                results[fixture_name] = {"status": "error", "error": str(e)}

        return results

    def validate_instagram_fixtures(self) -> dict:
        """Validate Instagram fixture files."""
        logger.info("Validating Instagram fixtures")

        instagram_fixtures = {
            "user": "instagram_user.json",
            "media": "instagram_media.json",
            "comments": "instagram_comments.json",
            "stories": "instagram_stories.json",
            "insights": "instagram_insights.json",
        }

        results = {}

        for fixture_name, filename in instagram_fixtures.items():
            try:
                file_path = self.fixtures_dir / filename
                if not file_path.exists():
                    self.errors.append(f"Instagram fixture {filename} not found")
                    results[fixture_name] = {"status": "missing", "error": "File not found"}
                    continue

                with open(file_path) as f:
                    data = json.load(f)

                # Validate based on fixture type
                if fixture_name == "user":
                    InstagramUser(**data)
                elif fixture_name == "media":
                    if "data" in data:
                        for item in data["data"]:
                            InstagramMedia(**item)
                    else:
                        InstagramMedia(**data)
                elif fixture_name == "comments":
                    if "data" in data:
                        for item in data["data"]:
                            InstagramComment(**item)
                    else:
                        InstagramComment(**data)
                elif fixture_name == "stories":
                    if "data" in data:
                        for item in data["data"]:
                            InstagramStory(**item)
                    else:
                        InstagramStory(**data)
                elif fixture_name == "insights":
                    if "data" in data:
                        for item in data["data"]:
                            InstagramInsight(**item)
                    else:
                        InstagramInsight(**data)

                results[fixture_name] = {
                    "status": "valid",
                    "file_size": file_path.stat().st_size,
                    "items_count": len(data.get("data", [data])),
                }

            except (json.JSONDecodeError, ValidationError) as e:
                self.errors.append(f"Instagram fixture {filename} validation error: {str(e)}")
                results[fixture_name] = {"status": "invalid", "error": str(e)}
            except Exception as e:
                self.errors.append(f"Instagram fixture {filename} unexpected error: {str(e)}")
                results[fixture_name] = {"status": "error", "error": str(e)}

        return results

    def validate_x_fixtures(self) -> dict:
        """Validate X fixture files."""
        logger.info("Validating X fixtures")

        x_fixtures = {
            "user": "x_user.json",
            "tweets": "x_tweets.json",
            "mentions": "x_mentions.json",
            "search": "x_search.json",
            "media": "x_media.json",
        }

        results = {}

        for fixture_name, filename in x_fixtures.items():
            try:
                file_path = self.fixtures_dir / filename
                if not file_path.exists():
                    self.errors.append(f"X fixture {filename} not found")
                    results[fixture_name] = {"status": "missing", "error": "File not found"}
                    continue

                with open(file_path) as f:
                    data = json.load(f)

                # Validate based on fixture type
                if fixture_name == "user":
                    XUser(**data)
                elif fixture_name == "tweets":
                    if "data" in data:
                        for item in data["data"]:
                            XTweet(**item)
                    else:
                        XTweet(**data)
                elif fixture_name == "mentions":
                    if "data" in data:
                        for item in data["data"]:
                            XTweet(**item)
                    else:
                        XTweet(**data)
                elif fixture_name == "search":
                    if "data" in data:
                        for item in data["data"]:
                            XTweet(**item)
                    else:
                        XTweet(**data)
                elif fixture_name == "media":
                    if "data" in data:
                        for item in data["data"]:
                            XMedia(**item)
                    else:
                        XMedia(**data)

                results[fixture_name] = {
                    "status": "valid",
                    "file_size": file_path.stat().st_size,
                    "items_count": len(data.get("data", [data])),
                }

            except (json.JSONDecodeError, ValidationError) as e:
                self.errors.append(f"X fixture {filename} validation error: {str(e)}")
                results[fixture_name] = {"status": "invalid", "error": str(e)}
            except Exception as e:
                self.errors.append(f"X fixture {filename} unexpected error: {str(e)}")
                results[fixture_name] = {"status": "error", "error": str(e)}

        return results

    def validate_all_fixtures(self) -> dict:
        """Validate all fixture files."""
        logger.info("Starting fixture validation for all platforms")

        results = {
            "youtube": self.validate_youtube_fixtures(),
            "twitch": self.validate_twitch_fixtures(),
            "tiktok": self.validate_tiktok_fixtures(),
            "instagram": self.validate_instagram_fixtures(),
            "x": self.validate_x_fixtures(),
        }

        # Calculate summary
        total_fixtures = 0
        valid_fixtures = 0
        missing_fixtures = 0
        invalid_fixtures = 0

        for platform_results in results.values():
            for fixture_result in platform_results.values():
                total_fixtures += 1
                if fixture_result["status"] == "valid":
                    valid_fixtures += 1
                elif fixture_result["status"] == "missing":
                    missing_fixtures += 1
                else:
                    invalid_fixtures += 1

        summary = {
            "total_fixtures": total_fixtures,
            "valid_fixtures": valid_fixtures,
            "missing_fixtures": missing_fixtures,
            "invalid_fixtures": invalid_fixtures,
            "validation_rate": valid_fixtures / total_fixtures if total_fixtures > 0 else 0,
            "errors": self.errors,
        }

        return {"platforms": results, "summary": summary}

    def print_results(self, results: dict):
        """Print formatted validation results."""
        print("\n" + "=" * 80)
        print("FIXTURE VALIDATION RESULTS")
        print("=" * 80)

        summary = results["summary"]
        print(f"Total Fixtures: {summary['total_fixtures']}")
        print(f"Valid Fixtures: {summary['valid_fixtures']}")
        print(f"Missing Fixtures: {summary['missing_fixtures']}")
        print(f"Invalid Fixtures: {summary['invalid_fixtures']}")
        print(f"Validation Rate: {summary['validation_rate']:.2%}")

        if summary["errors"]:
            print(f"\nErrors Found: {len(summary['errors'])}")
            for error in summary["errors"]:
                print(f"  ❌ {error}")

        print("\n" + "-" * 80)
        print("PLATFORM DETAILS")
        print("-" * 80)

        for platform_name, platform_results in results["platforms"].items():
            print(f"\n{platform_name.upper()}:")
            for fixture_name, fixture_result in platform_results.items():
                status = fixture_result["status"]
                if status == "valid":
                    print(
                        f"  ✅ {fixture_name}: {fixture_result['items_count']} items, {fixture_result['file_size']} bytes"
                    )
                elif status == "missing":
                    print(f"  ❌ {fixture_name}: Missing file")
                else:
                    print(f"  ❌ {fixture_name}: {status} - {fixture_result.get('error', 'Unknown error')}")

        print("\n" + "=" * 80)


def main():
    """Main function to run fixture validation."""
    logging.basicConfig(level=logging.INFO)

    validator = FixtureValidator()
    results = validator.validate_all_fixtures()

    validator.print_results(results)

    # Check if validation passed
    if results["summary"]["validation_rate"] >= 0.9:
        print("\n✅ Fixture validation PASSED")
        return 0
    else:
        print("\n❌ Fixture validation FAILED")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
