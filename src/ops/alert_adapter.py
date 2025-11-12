from __future__ import annotations

from platform.config.configuration import get_config
from platform.http.http_utils import REQUEST_TIMEOUT_SECONDS, resilient_post
from typing import Any

from fastapi import APIRouter, HTTPException, Request

from security.net_guard import SecurityError
from security.webhook_guard import verify_incoming
from ultimate_discord_intelligence_bot.tenancy import current_tenant


alert_router = APIRouter(prefix="/ops/alerts", tags=["alerts"])


def _format_alert_text(payload: dict[str, Any]) -> str:
    status = payload.get("status", "unknown")
    alerts = payload.get("alerts", [])
    lines: list[str] = [f"Alertmanager status: {status}"]
    for a in alerts:
        labels = a.get("labels", {})
        ann = a.get("annotations", {})
        name = labels.get("alertname", "(no name)")
        tenant = labels.get("tenant", labels.get("namespace", "-"))
        workspace = labels.get("workspace", labels.get("service", "-"))
        severity = labels.get("severity", "info")
        summary = ann.get("summary") or ann.get("title") or ""
        desc = ann.get("description") or ""
        lines.append(f"• [{severity}] {name} (tenant={tenant}, workspace={workspace})")
        if summary:
            lines.append(f"  - {summary}")
        if desc:
            lines.append(f"  - {desc}")
    return "\n".join(lines)


@alert_router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@alert_router.post("/alert")
async def receive_alert(request: Request) -> dict[str, str]:
    try:
        body = await request.body()
        ctx = current_tenant()
        verify_incoming(
            body,
            dict(request.headers),
            secret_id="alert",
            actor="alertmanager",
            tenant=ctx.tenant_id if ctx else None,
            workspace=ctx.workspace_id if ctx else None,
        )
    except SecurityError as e:
        raise HTTPException(status_code=401, detail=f"Webhook validation failed: {e}") from e
    import json

    try:
        payload = json.loads(body.decode("utf-8")) if body else {}
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=400, detail="Invalid JSON payload") from exc
    config = get_config()
    try:
        webhook = config.get_webhook("discord_alert")
    except ValueError:
        try:
            webhook = config.get_webhook("discord_private")
        except ValueError:
            try:
                webhook = config.get_webhook("discord")
            except ValueError as final_exc:
                raise HTTPException(status_code=503, detail="Discord alert webhook not configured") from final_exc
        else:
            return await _send_alert_payload(webhook, payload)
    return await _send_alert_payload(webhook, payload)


async def _send_alert_payload(webhook: str, payload: dict[str, Any]) -> dict[str, str]:
    content = _format_alert_text(payload)
    resp = resilient_post(
        webhook,
        json_payload={"content": content[:1900]},
        headers={"Content-Type": "application/json"},
        timeout_seconds=REQUEST_TIMEOUT_SECONDS,
    )
    if getattr(resp, "status_code", 400) >= 400:
        raise HTTPException(status_code=502, detail=f"Discord webhook error: {resp.text}")
    return {"status": "ok"}
