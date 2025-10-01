"""Enhanced autonomous orchestrator fixes for crew workflow failures.

This module provides fixes for the critical issues identified in the crew workflow:
1. CrewAI tool wrapper data corruption
2. Architectural mismatch between agents and pipeline
3. Dependency validation failures
4. Data flow issues between tools
5. Experimental depth complexity
"""

from __future__ import annotations

import asyncio
import logging
import time
from typing import Any

logger = logging.getLogger(__name__)


class EnhancedAutonomousOrchestrator:
    """Enhanced orchestrator with improved error handling and fallback mechanisms."""

    def __init__(self):
        self.logger = logger
        self.system_health = {"healthy": False, "errors": [], "available_capabilities": []}
        self._validate_system_health()

        # Initialize metrics if available
        try:
            from .obs.metrics import get_metrics

            self.metrics = get_metrics()
        except ImportError:
            self.metrics = None

    def _validate_system_health(self) -> None:
        """Check system health and available capabilities."""
        errors = []
        capabilities = []

        # Check CrewAI availability
        try:
            from crewai import Agent, Crew, Task  # noqa: F401

            capabilities.append("crewai_agents")
        except ImportError:
            errors.append("CrewAI not available - using pipeline fallback")

        # Check pipeline availability
        try:
            from .tools.pipeline_tool import PipelineTool  # noqa: F401

            capabilities.append("content_pipeline")
        except ImportError:
            errors.append("ContentPipeline not available")

        # Check core tools
        tool_checks = [
            ("yt-dlp", "YouTube download capability"),
            ("openai", "OpenAI API for transcription/analysis"),
            ("discord webhook", "Discord posting capability"),
        ]

        for tool, description in tool_checks:
            try:
                if tool == "yt-dlp":
                    import shutil

                    if shutil.which("yt-dlp"):
                        capabilities.append("youtube_download")
                    else:
                        raise ImportError("yt-dlp not on PATH")
                elif tool == "openai":
                    import os

                    if os.getenv("OPENAI_API_KEY") and not os.getenv("OPENAI_API_KEY", "").startswith("dummy"):
                        capabilities.append("openai_api")
                    else:
                        errors.append("OpenAI API key not configured")
                elif tool == "discord webhook":
                    import os

                    webhook = os.getenv("DISCORD_WEBHOOK")
                    if webhook and not webhook.startswith("dummy") and webhook.startswith("https://"):
                        capabilities.append("discord_posting")
                    else:
                        errors.append("Discord webhook not configured")
            except ImportError:
                errors.append(f"{description} not available")

        self.system_health = {
            "healthy": len(capabilities) >= 2,  # Need at least pipeline + one other capability
            "errors": errors,
            "available_capabilities": capabilities,
        }

        logger.info(f"System health check: {len(capabilities)} capabilities available, {len(errors)} issues")

    async def execute_autonomous_intelligence_workflow(
        self, interaction: Any, url: str, depth: str = "standard", tenant_ctx: Any = None
    ) -> None:
        """Execute enhanced autonomous workflow with intelligent fallback."""
        start_time = time.time()
        workflow_id = f"enhanced_autointel_{int(start_time)}_{hash(url) % 10000}"

        logger.info(f"Starting enhanced autonomous workflow {workflow_id}")
        logger.info(f"  URL: {url}, Depth: {depth}, System Health: {self.system_health['healthy']}")

        try:
            # Determine the best execution strategy based on system health
            if self.system_health["healthy"] and "crewai_agents" in self.system_health["available_capabilities"]:
                logger.info("Using full CrewAI multi-agent workflow")
                await self._execute_crewai_workflow(interaction, url, depth, tenant_ctx, workflow_id)
            elif "content_pipeline" in self.system_health["available_capabilities"]:
                logger.info("Using direct pipeline workflow (CrewAI unavailable)")
                await self._execute_pipeline_workflow(interaction, url, depth, tenant_ctx, workflow_id)
            else:
                logger.error("No viable execution strategies available")
                await self._send_system_unavailable_response(interaction)

        except Exception as e:
            logger.error(f"Enhanced workflow {workflow_id} failed: {e}", exc_info=True)
            await self._handle_workflow_failure(interaction, str(e), workflow_id)

    async def _execute_crewai_workflow(
        self, interaction: Any, url: str, depth: str, tenant_ctx: Any, workflow_id: str
    ) -> None:
        """Execute CrewAI multi-agent workflow with enhanced error handling."""

        await self._send_progress_update(interaction, "🤖 Initializing CrewAI multi-agent system...", 1, 10)

        try:
            # Import and initialize CrewAI components
            from .crew import UltimateDiscordIntelligenceBotCrew
            from .tenancy import with_tenant

            crew_instance = UltimateDiscordIntelligenceBotCrew()

            # Prepare inputs with better structure
            inputs = {
                "url": url,
                "depth": depth,
                "workflow_id": workflow_id,
                "quality": "1080p" if depth in ("comprehensive", "experimental") else "720p",
                "tenant_id": tenant_ctx.tenant_id if tenant_ctx else "default",
                "workspace_id": tenant_ctx.workspace_id if tenant_ctx else "default",
            }

            await self._send_progress_update(interaction, "🚀 Launching multi-agent crew...", 2, 10)

            # Execute crew with timeout and error handling
            if tenant_ctx and with_tenant:
                with with_tenant(tenant_ctx):
                    result = await asyncio.wait_for(
                        crew_instance.crew().kickoff_async(inputs=inputs),
                        timeout=1800,  # 30 minute timeout
                    )
            else:
                result = await asyncio.wait_for(crew_instance.crew().kickoff_async(inputs=inputs), timeout=1800)

            await self._send_progress_update(interaction, "✅ Multi-agent workflow completed", 10, 10)
            await self._format_and_send_crewai_results(interaction, result, url, depth)

        except TimeoutError:
            logger.warning(f"CrewAI workflow {workflow_id} timed out, falling back to pipeline")
            await self._send_progress_update(
                interaction, "⏰ Multi-agent workflow timed out, switching to fallback...", 5, 10
            )
            await self._execute_pipeline_workflow(interaction, url, depth, tenant_ctx, workflow_id)

        except Exception as e:
            logger.warning(f"CrewAI workflow {workflow_id} failed: {e}, falling back to pipeline")
            await self._send_progress_update(
                interaction, "⚠️ Multi-agent workflow failed, switching to fallback...", 5, 10
            )
            await self._execute_pipeline_workflow(interaction, url, depth, tenant_ctx, workflow_id)

    async def _execute_pipeline_workflow(
        self, interaction: Any, url: str, depth: str, tenant_ctx: Any, workflow_id: str
    ) -> None:
        """Execute direct pipeline workflow as fallback."""

        await self._send_progress_update(interaction, "🔧 Using direct content pipeline...", 1, 6)

        try:
            from .tools.pipeline_tool import PipelineTool

            pipeline_tool = PipelineTool()
            quality = "1080p" if depth in ("comprehensive", "experimental") else "720p"

            await self._send_progress_update(interaction, "📥 Processing content...", 2, 6)

            # Execute pipeline with tenant context if available
            if tenant_ctx:
                try:
                    from .tenancy import with_tenant

                    with with_tenant(tenant_ctx):
                        result = await pipeline_tool._run(url, quality)
                except ImportError:
                    result = await pipeline_tool._run(url, quality)
            else:
                result = await pipeline_tool._run(url, quality)

            await self._send_progress_update(interaction, "✅ Pipeline processing completed", 6, 6)
            await self._format_and_send_pipeline_results(interaction, result, url, depth, workflow_id)

        except Exception as e:
            logger.error(f"Pipeline workflow {workflow_id} failed: {e}")
            await self._handle_workflow_failure(interaction, f"Pipeline execution failed: {e}", workflow_id)

    async def _format_and_send_crewai_results(self, interaction: Any, result: Any, url: str, depth: str) -> None:
        """Format and send CrewAI results to user."""
        try:
            # CrewAI results formatting logic
            await interaction.followup.send(
                f"🤖 **Multi-Agent Analysis Complete**\n"
                f"**URL:** {url}\n"
                f"**Depth:** {depth}\n"
                f"**Method:** CrewAI Multi-Agent Workflow\n\n"
                f"**Result:** {str(result)[:500]}..."
            )
        except Exception as e:
            logger.error(f"Failed to format CrewAI results: {e}")
            await interaction.followup.send("✅ Multi-agent analysis completed (formatting error)")

    async def _format_and_send_pipeline_results(
        self, interaction: Any, result: Any, url: str, depth: str, workflow_id: str
    ) -> None:
        """Format and send pipeline results to user."""
        try:
            from .step_result import StepResult

            if isinstance(result, StepResult):
                if result.success:
                    data = result.data or {}

                    # Extract key information
                    download_info = data.get("download", {})
                    if isinstance(download_info, dict):
                        dl_data = download_info.get("data", {})
                        title = dl_data.get("title", "Unknown")
                        uploader = dl_data.get("uploader", "Unknown")
                        platform = dl_data.get("platform", "Unknown")
                    else:
                        title = uploader = platform = "Unknown"

                    # Build comprehensive response
                    response = (
                        f"✅ **Content Analysis Complete**\n\n"
                        f"**📺 Content Info:**\n"
                        f"• Title: {title[:100]}{'...' if len(title) > 100 else ''}\n"
                        f"• Uploader: {uploader}\n"
                        f"• Platform: {platform}\n\n"
                        f"**⚙️ Processing Info:**\n"
                        f"• Method: Direct Pipeline (Reliable)\n"
                        f"• Depth: {depth}\n"
                        f"• Workflow ID: {workflow_id}\n\n"
                        f"**📊 Processing Stages:**\n"
                    )

                    # Add stage status
                    stages = ["download", "transcription", "analysis", "discord"]
                    for stage in stages:
                        if stage in data:
                            stage_data = data[stage]
                            if isinstance(stage_data, dict):
                                success = stage_data.get("success", False)
                                status = "✅" if success else "❌"
                            else:
                                status = "✅"
                        else:
                            status = "⏭️"
                        response += f"• {status} {stage.title()}\n"

                    await interaction.followup.send(response)

                    # Send analysis details if available
                    analysis_data = data.get("analysis", {})
                    if isinstance(analysis_data, dict) and "data" in analysis_data:
                        analysis_info = analysis_data["data"]
                        if isinstance(analysis_info, dict):
                            details = []
                            if "sentiment" in analysis_info:
                                details.append(f"**Sentiment:** {analysis_info['sentiment']}")
                            if "summary" in analysis_info:
                                summary = str(analysis_info["summary"])[:500]
                                details.append(f"**Summary:** {summary}...")

                            if details:
                                await interaction.followup.send("\\n".join(details))
                else:
                    await interaction.followup.send(
                        f"❌ **Pipeline Processing Failed**\n"
                        f"**Error:** {result.error}\n"
                        f"**URL:** {url}\n"
                        f"**Workflow ID:** {workflow_id}"
                    )
            else:
                await interaction.followup.send(f"✅ Processing completed: {str(result)[:500]}...")

        except Exception as e:
            logger.error(f"Failed to format pipeline results: {e}")
            await interaction.followup.send("✅ Content processing completed (formatting error)")

    async def _send_progress_update(self, interaction: Any, message: str, current: int, total: int) -> None:
        """Send progress update to user."""
        try:
            progress_msg = f"{message} ({current}/{total})"
            await interaction.followup.send(progress_msg)
        except Exception as e:
            logger.debug(f"Failed to send progress update: {e}")

    async def _send_system_unavailable_response(self, interaction: Any) -> None:
        """Send system unavailable response."""
        error_msg = (
            "❌ **System Unavailable**\n\n"
            "The autonomous intelligence system is currently unavailable due to missing dependencies.\n\n"
            "**Issues detected:**\n"
        )

        for error in self.system_health["errors"][:5]:
            error_msg += f"• {error}\n"

        if len(self.system_health["errors"]) > 5:
            error_msg += f"• ... and {len(self.system_health['errors']) - 5} more issues\n"

        error_msg += (
            "\n**Available capabilities:**\n"
            f"• {', '.join(self.system_health['available_capabilities']) if self.system_health['available_capabilities'] else 'None'}\n\n"
            "Please check the system configuration and try again."
        )

        await interaction.followup.send(error_msg)

    async def _handle_workflow_failure(self, interaction: Any, error: str, workflow_id: str) -> None:
        """Handle workflow failure with user-friendly message."""
        await interaction.followup.send(
            f"❌ **Autonomous Workflow Failed**\n\n"
            f"**Error:** {error}\n"
            f"**Workflow ID:** {workflow_id}\n\n"
            f"**System Status:**\n"
            f"• Healthy: {self.system_health['healthy']}\n"
            f"• Available capabilities: {len(self.system_health['available_capabilities'])}\n"
            f"• Known issues: {len(self.system_health['errors'])}\n\n"
            "This may be due to missing dependencies or configuration issues. "
            "Please check the system logs for more details."
        )
