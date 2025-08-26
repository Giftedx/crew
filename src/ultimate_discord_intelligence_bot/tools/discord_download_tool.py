from __future__ import annotations

import os
import tempfile
from typing import Dict

import requests
from crewai_tools import BaseTool


class DiscordDownloadTool(BaseTool):
    """Download Discord-hosted attachments."""

    name = "Discord Download Tool"
    description = "Download Discord attachments"
    platform = "Discord"

    def _run(self, url: str, quality: str = "1080p") -> Dict[str, str]:
        """Download a file from a Discord attachment URL."""
        command_str = f"requests.get({url})"
        try:
            response = requests.get(url, stream=True, timeout=30)
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

    def run(self, url: str, quality: str = "1080p") -> Dict[str, str]:  # pragma: no cover - thin wrapper
        return self._run(url, quality)
