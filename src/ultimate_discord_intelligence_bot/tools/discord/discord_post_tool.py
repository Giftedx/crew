from __future__ import annotations
import json
import os
from pathlib import Path
from pydantic import Field
from platform.http.http_utils import (
    DEFAULT_RATE_LIMIT_RETRY,
    HTTP_RATE_LIMITED,
    HTTP_SUCCESS_NO_CONTENT,
    REQUEST_TIMEOUT_SECONDS,
    resilient_post,
    validate_public_https_url,
)
from platform.config.configuration import get_config
from core.time import default_utc_now
from platform.observability.metrics import get_metrics
from platform.core.step_result import StepResult
from .._base import BaseTool

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
    webhook_url: str | None = Field(default=None)

    def __init__(self, webhook_url: str | None = None):
        super().__init__()
        self.webhook_url = webhook_url or get_config("DISCORD_WEBHOOK")
        if not self.webhook_url:
            raise ValueError(
                "Discord webhook URL is not configured. Please set DISCORD_WEBHOOK in your environment or config."
            )
        validate_public_https_url(self.webhook_url)
        self._metrics = get_metrics()
        self._force_embeds = os.getenv("DISCORD_FORCE_EMBEDS", "0").strip() in {"1", "true", "True"}

    @staticmethod
    def _validate_webhook(url: str) -> str:
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
            return StepResult.skip(reason="empty content data")
        local_file_path = content_data.get("local_path")
        file_size_bytes: int | None = None
        if local_file_path:
            p = Path(str(local_file_path))
            if p.exists() and p.is_file():
                try:
                    file_size_bytes = p.stat().st_size
                except Exception:
                    file_size_bytes = None
        if file_size_bytes is None:
            raw = content_data.get("file_size")
            try:
                if isinstance(raw, (int, float)) or (isinstance(raw, str) and raw.isdigit()):
                    file_size_bytes = int(raw)
            except Exception:
                file_size_bytes = None
        if (
            not getattr(self, "_force_embeds", False)
            and file_size_bytes is not None
            and (file_size_bytes / (1024 * 1024) <= DISCORD_FILE_LIMIT_MB)
            and local_file_path
        ):
            return self._post_with_file_upload(content_data, drive_links)
        return self._post_with_embed_links(content_data, drive_links)

    def _post_with_embed_links(self, content_data: dict, drive_links: dict) -> StepResult:
        """Post using structured embeds with links (recommended approach)"""
        drive_skipped = isinstance(drive_links, dict) and drive_links.get("status") == "skipped"
        skip_message = (
            (str(drive_links.get("message")) if drive_skipped else "") if isinstance(drive_links, dict) else ""
        )
        embed = {
            "title": content_data.get("title", "New Content Available"),
            "description": f"📹 **Platform**: {content_data.get('platform', 'Unknown')}\n👤 **Creator**: {content_data.get('uploader', 'Unknown')}\n⏱️ **Duration**: {content_data.get('duration', 'Unknown')}\n📊 **Size**: {content_data.get('file_size', 'Unknown')}",
            "color": 65280,
            "thumbnail": {"url": "" if drive_skipped else drive_links.get("thumbnail", "")},
            "fields": [{"name": "i Drive Upload", "value": skip_message or "Drive upload skipped", "inline": False}]
            if drive_skipped
            else [
                {
                    "name": "🎥 Watch Online",
                    "value": f"[Google Drive Preview]({drive_links.get('preview_link', '')})",
                    "inline": True,
                },
                {
                    "name": "💾 Download",
                    "value": f"[Direct Download]({drive_links.get('direct_link', '')})",
                    "inline": True,
                },
            ],
            "footer": {"text": "CrewAI Content Monitor", "icon_url": "https://example.com/crewai-icon.png"},
            "timestamp": default_utc_now().isoformat(),
        }
        payload = {"username": "Content Monitor", "avatar_url": "https://example.com/bot-avatar.png", "embeds": [embed]}
        return self._send_webhook(payload)

    def _post_with_file_upload(self, content_data: dict, drive_links: dict) -> StepResult:
        """Post with direct file upload for smaller files"""
        local_file_path = content_data.get("local_path")
        if not local_file_path or not Path(local_file_path).exists():
            return self._post_with_embed_links(content_data, drive_links)
        with open(local_file_path, "rb") as fh:
            files = {
                "file": (Path(local_file_path).name, fh, "video/mp4"),
                "payload_json": (
                    None,
                    json.dumps(
                        {
                            "content": f"🎥 **{content_data.get('title', 'New Video')}**\nFrom: {content_data.get('uploader', 'Unknown')}\nPlatform: {content_data.get('platform', 'Unknown')}"
                        }
                    ),
                ),
            }
            try:
                response = resilient_post(self.webhook_url, files=files, timeout_seconds=REQUEST_TIMEOUT_SECONDS)
            except TypeError as exc:
                self._metrics.counter("tool_runs_total", labels={"tool": "discord_post", "outcome": "error"}).inc()
                return StepResult.fail(error=str(exc))
        return self._handle_response(response)

    def _post_simple_message(self, message: str, embeds: list[dict] | None = None) -> StepResult:
        """Post a simple content-only message (optionally with embeds).

        This path supports lightweight notifications and is tolerant of agents
        that pass just a message string instead of the richer content_data structure.
        """
        if not isinstance(message, str) or not message.strip():
            self._metrics.counter("tool_runs_total", labels={"tool": "discord_post", "outcome": "skipped"}).inc()
            return StepResult.skip(reason="empty message")
        payload: dict[str, object] = {"content": message}
        if isinstance(embeds, list) and embeds:
            payload["embeds"] = embeds
        return self._send_webhook(payload)

    def _send_webhook(self, payload: dict) -> StepResult:
        """Send webhook with rate limiting"""
        try:
            response = resilient_post(
                self.webhook_url,
                json_payload=payload,
                headers={"Content-Type": "application/json"},
                timeout_seconds=REQUEST_TIMEOUT_SECONDS,
            )
        except Exception as e:
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
                raw_json: object = getattr(response, "json", dict)()
                if isinstance(raw_json, dict):
                    data = raw_json
            except Exception:
                data = {}
            ra = data.get("retry_after") if isinstance(data, dict) else None
            retry_after: float = float(DEFAULT_RATE_LIMIT_RETRY)
            if isinstance(ra, int | float):
                if ra >= 0:
                    retry_after = float(ra)
            elif isinstance(ra, str):
                try:
                    candidate = float(ra)
                    if candidate >= 0:
                        retry_after = candidate
                except ValueError:
                    ...
            self._metrics.counter("tool_runs_total", labels={"tool": "discord_post", "outcome": "skipped"}).inc()
            return StepResult.skip(reason="rate_limited", data={"retry_after": retry_after})
        else:
            self._metrics.counter("tool_runs_total", labels={"tool": "discord_post", "outcome": "error"}).inc()
            return StepResult.fail(
                error=f"HTTP error: {response.status_code}", data={"status_code": int(response.status_code)}
            )

    def run(self, *args, **kwargs) -> StepResult:
        try:
            if "message" in kwargs or (args and isinstance(args[0], str)):
                message = str(kwargs.get("message", args[0] if args else ""))
                embeds = kwargs.get("embeds")
                if not isinstance(embeds, list):
                    embeds = None
                return self._post_simple_message(message, embeds=embeds)
            content_data: dict = {}
            drive_links: dict = {}
            if args:
                if len(args) == 1 and isinstance(args[0], dict):
                    content_data = args[0]
                    drive_links = kwargs.get("drive_links", {}) or {}
                elif len(args) >= 2 and isinstance(args[0], dict) and isinstance(args[1], dict):
                    content_data = args[0]
                    drive_links = args[1]
                else:
                    self._metrics.counter(
                        "tool_runs_total", labels={"tool": "discord_post", "outcome": "skipped"}
                    ).inc()
                    return StepResult.skip(reason="unsupported arguments")
            else:
                content_data = kwargs.get("content_data", {}) or {}
                drive_links = kwargs.get("drive_links", {}) or {}
                if not isinstance(content_data, dict) or not isinstance(drive_links, dict):
                    self._metrics.counter(
                        "tool_runs_total", labels={"tool": "discord_post", "outcome": "skipped"}
                    ).inc()
                    return StepResult.skip(reason="invalid payloads")
            return self._run(content_data, drive_links)
        except Exception as exc:
            self._metrics.counter("tool_runs_total", labels={"tool": "discord_post", "outcome": "error"}).inc()
            return StepResult.fail(error=str(exc))
