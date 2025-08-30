from __future__ import annotations

import os
import tempfile
from typing import ClassVar

from core.http_utils import REQUEST_TIMEOUT_SECONDS, resilient_get

from ._base import BaseTool


class DiscordDownloadTool(BaseTool[dict[str, str]]):
    """Download Discord-hosted attachments.

    Delegates HTTP GET handling (timeouts + legacy monkeypatch fallback) to
    `core.http_utils.resilient_get` which ensures tests with simplified
    `requests.get` doubles remain compatible without custom adapter logic.
    """

    name: str = "Discord Download Tool"
    description: str = "Download Discord attachments"
    platform: ClassVar[str] = "Discord"

    def _run(self, url: str, quality: str = "1080p") -> dict[str, str]:
        """Download a file from a Discord attachment URL."""
        command_str = f"requests.get({url})"
        try:
            response = resilient_get(url, stream=True, timeout_seconds=REQUEST_TIMEOUT_SECONDS)
            response.raise_for_status()
            suffix = os.path.splitext(url)[1]
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        tmp.write(chunk)
                local_path = tmp.name
            return {
                "status": "success",
                "platform": self.platform,
                "local_path": local_path,
                "command": command_str,
            }
        except Exception as exc:  # pragma: no cover - defensive path
            return {
                "status": "error",
                "platform": self.platform,
                "error": str(exc),
                "command": command_str,
            }

    def run(
        self, url: str, quality: str = "1080p"
    ) -> dict[str, str]:  # pragma: no cover - thin wrapper
        return self._run(url, quality)
