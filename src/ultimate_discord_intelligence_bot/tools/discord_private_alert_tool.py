"""Send internal alerts to a private Discord channel."""

from crewai.tools import BaseTool

from core.http_utils import (
    HTTP_SUCCESS_NO_CONTENT,
    REQUEST_TIMEOUT_SECONDS,
    resilient_post,
    validate_public_https_url,
)

_validate_webhook = validate_public_https_url


class DiscordPrivateAlertTool(BaseTool):
    """Post system alerts to a dedicated Discord channel.

    Uses shared HTTP helpers (`validate_public_https_url`, `resilient_post`)
    for secure URL validation, consistent timeout handling, and friendly
    fallback behaviour when tests monkeypatch `requests.post` with a reduced
    signature.
    """

    name: str = "Discord Private Alert Tool"
    description: str = "Send internal monitoring alerts to Discord"

    # Properly declare field for pydantic v2
    webhook_url: str = ""

    def __init__(self, webhook_url: str):
        super().__init__()
        self.webhook_url = _validate_webhook(webhook_url)

    def _run(
        self,
        message: str,
        metrics: dict[str, float] | None = None,
        thresholds: dict[str, float] | None = None,
    ) -> dict:
        warning = False
        if metrics:
            if thresholds:
                for key, limit in thresholds.items():
                    value = metrics.get(key)
                    if value is not None and value > limit:
                        warning = True
                        break
            metrics_text = "\n".join(f"{k}: {v}" for k, v in metrics.items())
            message = f"{message}\n```\n{metrics_text}\n```"
        if warning:
            message = f"⚠️ {message}"
        payload = {"content": message}
        try:
            response = resilient_post(
                self.webhook_url, json_payload=payload, timeout_seconds=REQUEST_TIMEOUT_SECONDS
            )
        except TypeError as exc:  # pragma: no cover - unrelated TypeError
            return {"status": "error", "error": str(exc)}
        except Exception as exc:  # pragma: no cover - network failure path
            return {"status": "error", "error": str(exc)}

        if response.status_code == HTTP_SUCCESS_NO_CONTENT:
            return {"status": "success"}
        else:
            return {"status": "error", "status_code": response.status_code, "error": getattr(response, 'text', '')}

    def run(self, *args, **kwargs):  # pragma: no cover
        return self._run(*args, **kwargs)
