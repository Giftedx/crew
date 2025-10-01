"""Tool for sending Discord private alerts per Copilot instructions.

Instrumentation:
    * tool_runs_total{tool="discord_private_alert", outcome}
    * Outcomes: success | error | skipped
    * No latency histogram (single lightweight POST)
"""

import ipaddress
import os
from urllib.parse import urlparse

from core.http_utils import resilient_post
from ultimate_discord_intelligence_bot.obs.metrics import get_metrics
from ultimate_discord_intelligence_bot.step_result import StepResult


class DiscordPrivateAlertTool:
    """Tool to send private Discord alerts via webhooks.

    Tests call the internal _run for deterministic control (monkeypatching requests.post).
    We provide both _run (core logic) and run (thin wrapper) for consistency with other tools.
    """

    def __init__(self, webhook_url: str | None = None):
        self.webhook_url = webhook_url or os.getenv("DISCORD_ALERT_WEBHOOK")
        self._metrics = get_metrics()

        if self.webhook_url and not self._is_valid_discord_url(self.webhook_url):  # early validation like tests expect
            raise ValueError("Invalid or insecure Discord webhook URL")

    # --- helpers ---
    def _is_valid_discord_url(self, url: str) -> bool:
        parsed = urlparse(url)
        if parsed.scheme != "https":
            return False
        host = parsed.hostname or ""
        # block private IPs
        try:
            ip = ipaddress.ip_address(host)
            if ip.is_private:
                return False
        except ValueError:
            # not an IP literal; allow discord domains only
            if not host.endswith("discord.com") and not host.endswith("discordapp.com"):
                return False
        return True

    def _run(self, message: str, metrics: dict | None = None, thresholds: dict | None = None) -> StepResult:
        if not self.webhook_url:
            self._metrics.counter(
                "tool_runs_total", labels={"tool": "discord_private_alert", "outcome": "skipped"}
            ).inc()
            return StepResult.skip(message="No webhook URL configured", platform="Discord", command="POST webhook")

        content = message
        metrics = metrics or {}
        thresholds = thresholds or {}

        # Prefix warning if any metric breaches threshold
        warnings: list[str] = []
        for k, v in metrics.items():
            thr = thresholds.get(k)
            # Support numeric thresholds only
            if isinstance(v, (int, float)) and isinstance(thr, (int, float)) and v > thr:  # noqa: UP038
                warnings.append(f"{k} above threshold ({v}>{thr})")
        if warnings:
            content = "⚠️ " + "; ".join(warnings) + f"\n{content}"

        # Append metrics inline for visibility
        if metrics:
            metrics_str = " | ".join(f"{k}={v}" for k, v in metrics.items())
            content = f"{content}\n``{metrics_str}``"

        try:
            response = resilient_post(
                self.webhook_url,
                json_payload={
                    "content": content,
                    "username": "Alert Bot",
                    "allowed_mentions": {"users": []},
                },
            )
            if getattr(response, "status_code", 0) in (200, 204):
                self._metrics.counter(
                    "tool_runs_total", labels={"tool": "discord_private_alert", "outcome": "success"}
                ).inc()
                return StepResult.ok(message_sent=True, content_sent=content[:200])
            self._metrics.counter("tool_runs_total", labels={"tool": "discord_private_alert", "outcome": "error"}).inc()
            return StepResult.fail(
                error=f"Discord API returned status {getattr(response, 'status_code', 'unknown')}",
                status_code=getattr(response, "status_code", None),
                platform="Discord",
                command="POST webhook",
            )
        except Exception as e:  # pragma: no cover - network/pathological
            self._metrics.counter("tool_runs_total", labels={"tool": "discord_private_alert", "outcome": "error"}).inc()
            return StepResult.fail(error=str(e), platform="Discord", command="POST webhook")

    def run(
        self, message: str, metrics: dict | None = None, thresholds: dict | None = None
    ) -> StepResult:  # pragma: no cover
        return self._run(message, metrics, thresholds)
