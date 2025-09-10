"""Tool for downloading Discord attachments per Copilot instructions.

Instrumentation:
    * tool_runs_total{tool="discord_download", outcome}
    * Outcomes: success | error | skipped
    * No latency histogram (small downloads; if future large usage emerges we can add)

Test Compatibility:
    Tests patch ``ultimate_discord_intelligence_bot.tools.discord_download_tool.resilient_get``.
    We therefore call ``resilient_get`` directly so the patch intercepts network IO.
"""

import os
import tempfile
from pathlib import Path

from pydantic import AnyHttpUrl, BaseModel

from core.http_utils import resilient_get  # exposed for test monkeypatching
from ultimate_discord_intelligence_bot.obs.metrics import get_metrics
from ultimate_discord_intelligence_bot.step_result import StepResult

from ._base import BaseTool

HTTP_OK = 200

_ENV_VAR = "DISCORD_DOWNLOAD_DIR"
_persistent_temp_dir: Path | None = None


def _resolve_download_dir(user_dir: Path | None) -> Path:
    if user_dir:
        return user_dir
    override = os.getenv(_ENV_VAR)
    if override:
        p = Path(override)
        p.mkdir(parents=True, exist_ok=True)
        return p
    # Avoid global mutation patterns; hold temp dir in function attribute
    if _resolve_download_dir.__dict__.get("_cached") is None:
        _resolve_download_dir._cached = Path(tempfile.mkdtemp(prefix="discord_dl_"))  # type: ignore[attr-defined]
    return _resolve_download_dir._cached  # type: ignore[attr-defined]


class DiscordDownloadTool(BaseTool):
    name: str = "Discord Download Tool"
    description: str = "Download a Discord attachment given its URL."
    platform = "Discord"

    # Provide structured schema so orchestrators / agents can validate inputs.
    class ArgsSchema(BaseModel):
        attachment_url: AnyHttpUrl | str
        filename: str | None = None

    args_schema = ArgsSchema

    def __init__(self, download_dir: Path | None = None):
        super().__init__()
        self.download_dir = _resolve_download_dir(download_dir)
        self._metrics = get_metrics()

    def run(
        self, attachment_url: str, filename: str | None = None, **kwargs
    ) -> StepResult:  # kwargs for forward compat
        # If passed an object with the ArgsSchema shape (some frameworks do this), unwrap via duck typing.
        if hasattr(attachment_url, "attachment_url"):
            try:
                url_val = getattr(attachment_url, "attachment_url")
                file_val = getattr(attachment_url, "filename", None)
                return self._run(str(url_val), file_val)
            except Exception:
                return StepResult.fail(error="Invalid ArgsSchema instance")
        return self._run(str(attachment_url), filename)

    def _run(self, attachment_url: str, filename: str | None = None) -> StepResult:
        if not attachment_url:
            self._metrics.counter("tool_runs_total", labels={"tool": "discord_download", "outcome": "skipped"}).inc()
            return StepResult.ok(skipped=True, reason="No attachment URL provided")
        try:
            # Use resilient_get internally but preserve legacy provenance string expected by tests.
            response = resilient_get(attachment_url, stream=True, timeout_seconds=30)
            command_str = f"requests.get {attachment_url}"  # maintain backward-compatible provenance prefix
            if hasattr(response, "raise_for_status"):
                try:
                    response.raise_for_status()
                except Exception as http_err:  # propagate as failure StepResult
                    self._metrics.counter(
                        "tool_runs_total", labels={"tool": "discord_download", "outcome": "error"}
                    ).inc()
                    return StepResult.fail(error=str(http_err), command=command_str, platform=self.platform)
            status_code = getattr(response, "status_code", HTTP_OK)
            if not isinstance(status_code, int):
                status_code = HTTP_OK
            if status_code != HTTP_OK:
                self._metrics.counter("tool_runs_total", labels={"tool": "discord_download", "outcome": "error"}).inc()
                return StepResult.fail(
                    error=f"Failed to download: HTTP {status_code}",
                    data={"status_code": status_code},
                    command=command_str,
                )
            if not filename:
                filename = attachment_url.split("/")[-1].split("?")[0]
            file_path = self.download_dir / filename
            with open(file_path, "wb") as f:
                for chunk in getattr(response, "iter_content", lambda **_: [])(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            self._metrics.counter("tool_runs_total", labels={"tool": "discord_download", "outcome": "success"}).inc()
            return StepResult.ok(
                file_path=str(file_path),
                local_path=str(file_path),
                size=file_path.stat().st_size,
                success=True,
                platform=self.platform,
                command=command_str,
            )
        except Exception as e:  # pragma: no cover - network/pathological errors
            self._metrics.counter("tool_runs_total", labels={"tool": "discord_download", "outcome": "error"}).inc()
            return StepResult.fail(error=str(e), command=f"requests.get {attachment_url}")
