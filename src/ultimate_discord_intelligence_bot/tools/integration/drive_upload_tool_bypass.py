"""Bypass variant of Google Drive upload that returns local file links.

This tool is intended for environments where Google Drive credentials are not
available or uploads are disabled. It mimics the output structure of
``DriveUploadTool`` while avoiding any external API calls, allowing downstream
components to proceed with local file references.
"""

from __future__ import annotations

import os
from platform.core.step_result import StepResult
from platform.observability.metrics import get_metrics
from typing import Any, ClassVar

from .._base import BaseTool


class DriveUploadToolBypass(BaseTool[StepResult]):
    name: str = "Google Drive Upload Tool (Bypass)"
    description: str = "Bypass uploads and generate local/shareable links without contacting Google Drive"
    model_config: ClassVar[dict[str, Any]] = {"extra": "allow"}

    def __init__(self) -> None:
        super().__init__()
        self._metrics = get_metrics()

    def _build_links(self, file_path: str) -> dict[str, str]:
        # Use absolute path for file:// links to improve compatibility
        abs_path = os.path.abspath(file_path)
        file_url = f"file://{abs_path}"
        return {
            "preview_link": file_url,
            "direct_link": file_url,
            "view_link": file_url,
            "thumbnail": file_url,
        }

    def run(self, file_path: str, platform: str | None = None, *args: Any, **kwargs: Any) -> StepResult:
        try:
            if not file_path or not isinstance(file_path, str):
                self._metrics.counter(
                    "tool_runs_total", labels={"tool": "drive_upload_bypass", "outcome": "error"}
                ).inc()
                return StepResult.bad_request("file_path must be a non-empty string")

            if not os.path.exists(file_path):
                self._metrics.counter(
                    "tool_runs_total", labels={"tool": "drive_upload_bypass", "outcome": "error"}
                ).inc()
                return StepResult.not_found(error=f"File not found: {file_path}")

            file_name = os.path.basename(file_path)
            file_size: int | None
            try:
                file_size = int(os.path.getsize(file_path))
            except Exception:
                file_size = None

            links = self._build_links(file_path)
            self._metrics.counter("tool_runs_total", labels={"tool": "drive_upload_bypass", "outcome": "success"}).inc()
            # Mirror shape of DriveUploadTool return for drop-in compatibility
            return StepResult.ok(
                data={
                    "file_id": None,
                    "file_name": file_name,
                    "file_size": file_size,
                    "links": links,
                    "bypassed": True,
                    "platform": platform or "local",
                }
            )
        except Exception as exc:  # pragma: no cover - defensive guard
            self._metrics.counter("tool_runs_total", labels={"tool": "drive_upload_bypass", "outcome": "error"}).inc()
            return StepResult.fail(error=str(exc), platform="Bypass", command="upload-bypass")


__all__ = ["DriveUploadToolBypass"]
