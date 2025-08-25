"""Send internal alerts to a private Discord channel."""

import ipaddress
from typing import Dict, Optional
from urllib.parse import urlparse

import requests
from crewai_tools import BaseTool


def _validate_webhook(url: str) -> str:
    """Validate webhook URL to ensure it's HTTPS and publicly routable."""
    parsed = urlparse(url)
    if parsed.scheme != "https":
        raise ValueError("Discord webhook must use https")
    if not parsed.hostname:
        raise ValueError("Discord webhook must include a host")
    try:
        ip = ipaddress.ip_address(parsed.hostname)
    except ValueError:
        return url
    if not ip.is_global:
        raise ValueError("Discord webhook IP must be globally routable")
    return url


class DiscordPrivateAlertTool(BaseTool):
    """Post system alerts to a dedicated Discord channel."""

    name: str = "Discord Private Alert Tool"
    description: str = "Send internal monitoring alerts to Discord"

    def __init__(self, webhook_url: str):
        super().__init__()
        self.webhook_url = _validate_webhook(webhook_url)

    def _run(self, message: str, metrics: Optional[Dict[str, float]] = None) -> dict:
        if metrics:
            metrics_text = "\n".join(f"{k}: {v}" for k, v in metrics.items())
            message = f"{message}\n```\n{metrics_text}\n```"
        payload = {"content": message}
        try:
            response = requests.post(self.webhook_url, json=payload)
        except Exception as exc:  # pragma: no cover - network failure path
            return {"status": "error", "error": str(exc)}

        if response.status_code == 204:
            return {"status": "success"}
        else:
            return {"status": "error", "status_code": response.status_code, "error": response.text}

    def run(self, *args, **kwargs):  # pragma: no cover
        return self._run(*args, **kwargs)

