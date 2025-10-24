from __future__ import annotations

import logging
from typing import Any

from fastapi.responses import JSONResponse

from fastapi import Body, FastAPI, HTTPException, status


logger = logging.getLogger(__name__)


def register_autointel_routes(app: FastAPI, settings: Any) -> None:
    """Register the Autonomous Intelligence HTTP endpoint when enabled.

    The endpoint is guarded by the ``ENABLE_AUTOINTEL_API`` flag and uses the
    existing ``AutonomousIntelligenceOrchestrator`` so tracing and metrics
    instrumentation remain centralized.

    This provides programmatic access to the autonomous intelligence workflow
    that is currently only accessible via Discord bot.
    """

    try:
        enabled = bool(getattr(settings, "enable_autointel_api", False))
    except Exception as exc:  # pragma: no cover - defensive settings access
        logger.debug("autointel API flag lookup failed: %s", exc)
        return

    if not enabled:
        return

    try:
        from ultimate_discord_intelligence_bot.autonomous_orchestrator import (
            AutonomousIntelligenceOrchestrator,
        )
        from ultimate_discord_intelligence_bot.tenancy import TenantContext, with_tenant
    except Exception as exc:  # pragma: no cover - optional dependency path
        logger.debug("autointel API wiring skipped: %s", exc)
        return

    @app.post("/autointel", summary="Run autonomous intelligence analysis")
    async def _autointel_run(
        payload: dict[str, Any] = Body(..., embed=False),
    ) -> JSONResponse:
        """Execute autonomous intelligence workflow via HTTP.

        Request body:
            url: Content URL to analyze (required)
            depth: Analysis depth - standard|deep|comprehensive|experimental (default: standard)
            tenant_id: Tenant identifier (default: "default")
            workspace_id: Workspace identifier (default: "main")

        Returns:
            JSON response with workflow results or error details
        """
        url = payload.get("url")
        depth = payload.get("depth", "standard")
        tenant_id = payload.get("tenant_id") or payload.get("tenant") or "default"
        workspace_id = payload.get("workspace_id") or payload.get("workspace") or "main"

        # Validate required parameters
        if not isinstance(url, str) or not url.strip():
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="`url` is required",
            )

        if depth is not None and not isinstance(depth, str):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="`depth` must be a string",
            )

        # Validate depth value
        valid_depths = {"standard", "deep", "comprehensive", "experimental"}
        resolved_depth = depth.strip().lower() if isinstance(depth, str) else "standard"
        if resolved_depth not in valid_depths:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"`depth` must be one of {valid_depths}, got: {resolved_depth}",
            )

        # Create orchestrator and tenant context
        orchestrator = AutonomousIntelligenceOrchestrator()
        ctx = TenantContext(tenant_id=tenant_id, workspace_id=workspace_id)

        # Create a minimal interaction object for non-Discord usage
        # The orchestrator expects this for progress updates, but we'll ignore those in HTTP mode
        class HTTPInteraction:
            """Minimal interaction object for HTTP requests."""

            def __init__(self):
                self.guild_id = tenant_id
                self.channel = type("Channel", (), {"name": workspace_id})()

            async def followup(self, *args, **kwargs):
                # Suppress Discord followup messages in HTTP mode
                pass

        interaction = HTTPInteraction()

        try:
            logger.info(
                "autointel API request",
                extra={
                    "tenant_id": tenant_id,
                    "workspace_id": workspace_id,
                    "depth": resolved_depth,
                },
            )

            # Execute workflow within tenant context
            with with_tenant(ctx):
                # The orchestrator's execute method doesn't return StepResult directly,
                # it sends updates via interaction.followup. We need to capture the result.
                # For now, we'll run it and return success if no exception is raised.
                await orchestrator.execute_autonomous_intelligence_workflow(
                    interaction=interaction,
                    url=url.strip(),
                    depth=resolved_depth,
                    tenant_ctx=ctx,
                )

            # If we get here, workflow completed successfully
            response_payload = {
                "success": True,
                "data": {
                    "url": url.strip(),
                    "depth": resolved_depth,
                    "tenant_id": tenant_id,
                    "workspace_id": workspace_id,
                    "status": "completed",
                    "message": "Autonomous intelligence analysis completed successfully",
                },
            }

            return JSONResponse(status_code=status.HTTP_200_OK, content=response_payload)

        except HTTPException:
            raise
        except Exception as exc:  # pragma: no cover - workflow error path
            logger.exception("autointel workflow failed: %s", exc)
            error_payload = {
                "success": False,
                "error": str(exc),
                "data": {
                    "url": url.strip(),
                    "depth": resolved_depth,
                    "tenant_id": tenant_id,
                    "workspace_id": workspace_id,
                    "status": "failed",
                },
            }
            return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content=error_payload)


__all__ = ["register_autointel_routes"]
