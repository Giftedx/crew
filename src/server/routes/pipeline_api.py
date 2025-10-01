from __future__ import annotations

import logging
from typing import Any

from fastapi import Body, FastAPI, HTTPException, status
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)


def register_pipeline_routes(app: FastAPI, settings: Any) -> None:
    """Register the ContentPipeline HTTP trigger when enabled.

    The endpoint is guarded by the ``ENABLE_PIPELINE_RUN_API`` flag and uses the
    existing ``PipelineTool`` implementation so budgeting, tracing, and metrics
    instrumentation remain centralised.
    """

    try:
        enabled = bool(getattr(settings, "enable_pipeline_run_api"))
    except Exception as exc:  # pragma: no cover - defensive settings access
        logger.debug("pipeline API flag lookup failed: %s", exc)
        return

    if not enabled:
        return

    try:
        from ultimate_discord_intelligence_bot.step_result import StepResult
        from ultimate_discord_intelligence_bot.tenancy import TenantContext, with_tenant
        from ultimate_discord_intelligence_bot.tools.pipeline_tool import PipelineTool
    except Exception as exc:  # pragma: no cover - optional dependency path
        logger.debug("pipeline API wiring skipped: %s", exc)
        return

    @app.post("/pipeline/run", summary="Run the content pipeline")
    async def _pipeline_run(payload: dict[str, Any] = Body(..., embed=False)) -> JSONResponse:
        url = payload.get("url")
        quality = payload.get("quality")
        tenant_id = payload.get("tenant_id") or payload.get("tenant") or "default"
        workspace_id = payload.get("workspace_id") or payload.get("workspace") or "main"

        if not isinstance(url, str) or not url.strip():
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="`url` is required")

        if quality is not None and not isinstance(quality, str):
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="`quality` must be a string")

        resolved_quality = quality.strip() if isinstance(quality, str) else None

        tool = PipelineTool()
        ctx = TenantContext(tenant_id=tenant_id, workspace_id=workspace_id)

        try:
            logger.info("pipeline API request", extra={"tenant_id": tenant_id, "workspace_id": workspace_id})
            with with_tenant(ctx):
                result: StepResult = await tool._run_async(url.strip(), resolved_quality or "1080p")
        except HTTPException:
            raise
        except Exception as exc:  # pragma: no cover - pipeline error path
            logger.exception("pipeline run failed: %s", exc)
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Pipeline execution failed")

        response_payload = result.to_dict()
        data = response_payload.setdefault("data", {})
        if isinstance(data, dict):
            data.setdefault("tenant_id", tenant_id)
            data.setdefault("workspace_id", workspace_id)

        http_status = status.HTTP_200_OK if result.success else status.HTTP_502_BAD_GATEWAY
        return JSONResponse(status_code=http_status, content=response_payload)


__all__ = ["register_pipeline_routes"]
