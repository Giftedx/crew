from __future__ import annotations

import json
import os
from pathlib import Path

from core.http_utils import (
    DEFAULT_RATE_LIMIT_RETRY,
    HTTP_RATE_LIMITED,
    HTTP_SUCCESS_NO_CONTENT,
    REQUEST_TIMEOUT_SECONDS,
    resilient_post,
    validate_public_https_url,
)
from core.time import default_utc_now
from pydantic import Field

from ultimate_discord_intelligence_bot.obs.metrics import get_metrics
from ultimate_discord_intelligence_bot.step_result import StepResult

from ._base import BaseTool

# ---------------------------------------------------------------------------
# Constants (avoid magic numbers in logic)
# ---------------------------------------------------------------------------
# Conservative default: many servers/webhooks cap uploads around 8MB.
# Prefer embeds for larger media to avoid HTTP 413 errors.
DISCORD_FILE_LIMIT_MB = 7.5


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
        # Optional env switch to force embed-only posts regardless of file size
        self._force_embeds = os.getenv("DISCORD_FORCE_EMBEDS", "0").strip() in {"1", "true", "True"}

    @staticmethod
    def _validate_webhook(url: str) -> str:  # backward compatibility shim
        return validate_public_https_url(url)

    def _run(self, content_data: dict, drive_links: dict) -> StepResult:
        """Post content notification with proper formatting

        Prefer link-based embeds by default. Only attempt direct file upload when:
        - a local file path exists AND
        - the actual file size on disk is within Discord's typical limit.
        This avoids 413 Payload Too Large errors when metadata is missing or stale.
        """
        if not content_data:
            self._metrics.counter("tool_runs_total", labels={"tool": "discord_post", "outcome": "skipped"}).inc()
            return StepResult.ok(skipped=True, reason="empty content data")

        # Prefer real on-disk size if we have a local path; fallback to metadata
        local_file_path = content_data.get("local_path")
        file_size_bytes: int | None = None
        if local_file_path:
            p = Path(str(local_file_path))
            if p.exists() and p.is_file():
                try:
                    file_size_bytes = p.stat().st_size
                except Exception:  # pragma: no cover - fs failure fallback
                    file_size_bytes = None
        if file_size_bytes is None:
            # Some downloaders provide numeric bytes; handle strings like "12345" too
            raw = content_data.get("file_size")
            try:
                if isinstance(raw, (int, float)):
                    file_size_bytes = int(raw)
                elif isinstance(raw, str) and raw.isdigit():
                    file_size_bytes = int(raw)
            except Exception:  # pragma: no cover - defensive
                file_size_bytes = None

        if (
            not getattr(self, "_force_embeds", False)
            and file_size_bytes is not None
            and (file_size_bytes / (1024 * 1024)) <= DISCORD_FILE_LIMIT_MB
            and local_file_path
        ):
            return self._post_with_file_upload(content_data, drive_links)
        # Default to embeds for safety
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
            "timestamp": default_utc_now().isoformat(),
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
