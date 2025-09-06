from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

from pydantic import Field

from core.http_utils import (
    DEFAULT_RATE_LIMIT_RETRY,
    HTTP_RATE_LIMITED,
    HTTP_SUCCESS_NO_CONTENT,
    REQUEST_TIMEOUT_SECONDS,
    resilient_post,
    validate_public_https_url,
)
from ultimate_discord_intelligence_bot.obs.metrics import get_metrics
from ultimate_discord_intelligence_bot.step_result import StepResult

from ._base import BaseTool

# ---------------------------------------------------------------------------
# Constants (avoid magic numbers in logic)
# ---------------------------------------------------------------------------
DISCORD_FILE_LIMIT_MB = 100  # Typical limit for standard servers (may vary)


class DiscordPostTool(BaseTool[StepResult]):
    """Post messages, embeds, and small file uploads to Discord via webhook.

    HTTP concerns (URL validation, standard timeouts, legacy monkeypatch
    compatibility for tests) are delegated to `core.http_utils` helpers
    (`validate_public_https_url`, `resilient_post`) to avoid duplicated
    request construction logic across tools.
    """

    name: str = "Discord Post Tool"
    description: str = "Post content notifications to Discord with proper formatting"

    webhook_url: str = Field(default="")

    def __init__(self, webhook_url: str):
        # Use BaseTool/Pydantic init for proper field setup then override value
        super().__init__()
        object.__setattr__(self, "webhook_url", validate_public_https_url(webhook_url))
        self._metrics = get_metrics()

    @staticmethod
    def _validate_webhook(url: str) -> str:  # backward compatibility shim
        return validate_public_https_url(url)

    def _run(self, content_data: dict, drive_links: dict) -> StepResult:
        """Post content notification with proper formatting"""
        if not content_data:
            self._metrics.counter("tool_runs_total", labels={"tool": "discord_post", "outcome": "skipped"}).inc()
            return StepResult.ok(skipped=True, reason="empty content data")
        # Check file size for direct upload vs link sharing
        try:
            file_size_mb = int(content_data.get("file_size", 0)) / (1024 * 1024)
        except Exception:  # pragma: no cover - defensive parsing
            file_size_mb = 0

        if file_size_mb <= DISCORD_FILE_LIMIT_MB:  # Within Discord limits for most servers
            return self._post_with_file_upload(content_data, drive_links)
        return self._post_with_embed_links(content_data, drive_links)

    def _post_with_embed_links(self, content_data: dict, drive_links: dict) -> StepResult:
        """Post using structured embeds with links (recommended approach)"""

        embed = {
            "title": content_data.get("title", "New Content Available"),
            "description": f"📹 **Platform**: {content_data.get('platform', 'Unknown')}\n"
            f"👤 **Creator**: {content_data.get('uploader', 'Unknown')}\n"
            f"⏱️ **Duration**: {content_data.get('duration', 'Unknown')}\n"
            f"📊 **Size**: {content_data.get('file_size', 'Unknown')}",
            "color": 0x00FF00,  # Green for success
            "thumbnail": {
                # Drive metadata may be missing if upload failed but we still
                # want to send a notification. Using ``get`` avoids KeyError
                # while allowing Discord to render an empty thumbnail slot.
                "url": drive_links.get("thumbnail", "")
            },
            "fields": [
                {
                    "name": "🎥 Watch Online",
                    # Safely access links; an empty string renders a plain label
                    # rather than raising an exception and losing the update.
                    "value": f"[Google Drive Preview]({drive_links.get('preview_link', '')})",
                    "inline": True,
                },
                {
                    "name": "💾 Download",
                    "value": f"[Direct Download]({drive_links.get('direct_link', '')})",
                    "inline": True,
                },
            ],
            "footer": {
                "text": "CrewAI Content Monitor",
                "icon_url": "https://example.com/crewai-icon.png",
            },
            # Use explicit UTC to avoid naive timestamps which complicate downstream parsing
            "timestamp": datetime.now(UTC).isoformat(),
        }

        payload = {
            "username": "Content Monitor",
            "avatar_url": "https://example.com/bot-avatar.png",
            "embeds": [embed],
        }

        return self._send_webhook(payload)

    def _post_with_file_upload(self, content_data: dict, drive_links: dict) -> StepResult:
        """Post with direct file upload for smaller files"""

        local_file_path = content_data.get("local_path")
        if not local_file_path or not Path(local_file_path).exists():
            # Fallback to link posting
            return self._post_with_embed_links(content_data, drive_links)

        # Upload file directly to Discord. A context manager ensures the file
        # handle is closed even if the request fails.
        with open(local_file_path, "rb") as fh:
            files = {
                "file": (Path(local_file_path).name, fh, "video/mp4"),
                "payload_json": (
                    None,
                    json.dumps(
                        {
                            "content": f"🎥 **{content_data.get('title', 'New Video')}**\n"
                            f"From: {content_data.get('uploader', 'Unknown')}\n"
                            f"Platform: {content_data.get('platform', 'Unknown')}"
                        }
                    ),
                ),
            }

            try:
                response = resilient_post(self.webhook_url, files=files, timeout_seconds=REQUEST_TIMEOUT_SECONDS)
            except TypeError as exc:  # pragma: no cover - unrelated TypeError
                self._metrics.counter("tool_runs_total", labels={"tool": "discord_post", "outcome": "error"}).inc()
                return StepResult.fail(error=str(exc))

        return self._handle_response(response)

    def _send_webhook(self, payload: dict) -> StepResult:
        """Send webhook with rate limiting"""
        try:
            response = resilient_post(
                self.webhook_url,
                json_payload=payload,
                headers={"Content-Type": "application/json"},
                timeout_seconds=REQUEST_TIMEOUT_SECONDS,
            )
        except Exception as e:  # pragma: no cover
            self._metrics.counter("tool_runs_total", labels={"tool": "discord_post", "outcome": "error"}).inc()
            return StepResult.fail(error=str(e))
        return self._handle_response(response)

    def _handle_response(self, response) -> StepResult:
        """Handle Discord API response with rate limiting"""
        if response.status_code == HTTP_SUCCESS_NO_CONTENT:
            self._metrics.counter("tool_runs_total", labels={"tool": "discord_post", "outcome": "success"}).inc()
            return StepResult.ok()
        elif response.status_code == HTTP_RATE_LIMITED:
            data: dict[str, object] = {}
            try:
                raw_json: object = getattr(response, "json", lambda: {})()
                if isinstance(raw_json, dict):
                    data = raw_json  # narrow to dict[str, object]
            except Exception:  # pragma: no cover - malformed JSON
                data = {}
            ra = data.get("retry_after") if isinstance(data, dict) else None
            retry_after: float = float(DEFAULT_RATE_LIMIT_RETRY)
            if isinstance(ra, int | float):  # Compatible union syntax
                if ra >= 0:
                    retry_after = float(ra)
            elif isinstance(ra, str):
                try:
                    candidate = float(ra)
                    if candidate >= 0:
                        retry_after = candidate
                except ValueError:  # pragma: no cover - ignore non-numeric string
                    # Non-numeric retry_after -> fallback to default; explicit except avoids blanket swallow
                    ...
            self._metrics.counter("tool_runs_total", labels={"tool": "discord_post", "outcome": "skipped"}).inc()
            return StepResult.ok(skipped=True, reason="rate_limited", data={"retry_after": retry_after})
        else:
            self._metrics.counter("tool_runs_total", labels={"tool": "discord_post", "outcome": "error"}).inc()
            return StepResult.fail(
                error=f"HTTP error: {response.status_code}", data={"status_code": int(response.status_code)}
            )

    # Public run method to align with pipeline expectations
    def run(self, *args, **kwargs) -> StepResult:  # pragma: no cover - thin wrapper
        try:
            return self._run(*args, **kwargs)
        except Exception as exc:  # pragma: no cover - unexpected
            self._metrics.counter("tool_runs_total", labels={"tool": "discord_post", "outcome": "error"}).inc()
            return StepResult.fail(error=str(exc))
