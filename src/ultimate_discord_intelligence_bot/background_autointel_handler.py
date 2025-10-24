"""Background /autointel Command Handler - No Time Limits.

This module provides a modified /autointel command handler that uses the
BackgroundIntelligenceWorker for unlimited analysis time. It bypasses Discord's
15-minute interaction token limit by:

1. Immediately acknowledging the request (< 3 seconds)
2. Starting background analysis with no time constraints
3. Delivering results via webhook when complete (even hours later)
4. Supporting result retrieval for orphaned workflows

Usage:
    Replace the standard /autointel handler with this implementation to enable
    rigorous, comprehensive fact-checking without arbitrary time limits.
"""

from __future__ import annotations

import contextlib
import logging
import os
from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from discord import Interaction
    from ultimate_discord_intelligence_bot.autonomous_orchestrator import (
        AutonomousIntelligenceOrchestrator,
    )
    from ultimate_discord_intelligence_bot.background_intelligence_worker import (
        BackgroundIntelligenceWorker,
    )

logger = logging.getLogger(__name__)


async def handle_autointel_background(
    interaction: Interaction,
    orchestrator: AutonomousIntelligenceOrchestrator,
    background_worker: BackgroundIntelligenceWorker,
    url: str,
    depth: str = "standard",
) -> None:
    """Handle /autointel command with background processing (no time limits).

    This implementation immediately acknowledges the request and starts analysis
    in the background. Results are delivered via webhook, allowing comprehensive
    fact-checking that can take hours if needed.

    Args:
        interaction: Discord interaction object
        orchestrator: The autonomous intelligence orchestrator
        background_worker: Background task worker
        url: Content URL to analyze
        depth: Analysis depth (quick/standard/deep/comprehensive/experimental)
    """
    from obs import metrics

    try:
        # Defer immediately to prevent timeout (if not already deferred)
        if not interaction.response.is_done():
            await interaction.response.defer(ephemeral=False)

        # Get webhook URL from environment
        webhook_url = os.getenv("DISCORD_WEBHOOK")
        if not webhook_url:
            await interaction.followup.send(
                "❌ **Configuration Error**\n\n"
                "Background processing requires `DISCORD_WEBHOOK` to be configured.\n"
                "Please set the webhook URL in your `.env` file.",
                ephemeral=True,
            )
            return

        # Start background workflow (returns immediately)
        workflow_id = await background_worker.start_background_workflow(
            url=url,
            depth=depth,
            webhook_url=webhook_url,
            user_id=str(interaction.user.id) if hasattr(interaction, "user") else None,
            channel_id=str(interaction.channel_id) if hasattr(interaction, "channel_id") else None,
            metadata={
                "guild_id": str(interaction.guild_id) if hasattr(interaction, "guild_id") else None,
                "command": "/autointel",
            },
        )

        # Send acknowledgment with workflow ID (this happens in < 3 seconds)
        acknowledgment = (
            "# 🚀 Intelligence Analysis Started\n\n"
            f"**Workflow ID:** `{workflow_id}`\n"
            f"**URL:** {url}\n"
            f"**Analysis Depth:** `{depth}`\n"
            f"**Processing Mode:** Background (no time limits)\n\n"
            "---\n\n"
            "## What's Happening Now\n\n"
            "Your request has been accepted and is now processing in the background. "
            "This analysis will run for as long as needed to ensure comprehensive fact-checking "
            "and rigorous validation of all claims.\n\n"
            "**Key Features:**\n"
            "• ✅ **No Time Constraints** - Analysis proceeds at the pace required for accuracy\n"
            "• ✅ **Comprehensive Research** - Every claim is independently verified\n"
            "• ✅ **Automatic Delivery** - Results will be posted here when complete\n"
            "• ✅ **Retrievable** - Use `/retrieve_results workflow_id:{workflow_id}` if needed\n\n"
            "---\n\n"
            "## Expected Timeline\n\n"
            f"- **Quick analysis:** ~2-5 minutes\n"
            f"- **Standard analysis:** ~5-15 minutes\n"
            f"- **Deep analysis:** ~15-45 minutes\n"
            f"- **Comprehensive/Experimental:** ~45+ minutes (thorough fact-finding)\n\n"
            "_Note: Analysis quality is never rushed. The system will take as long as "
            "needed to ensure rigorous validation._"
        )

        await interaction.followup.send(acknowledgment)

        logger.info(f"✅ Background /autointel started: workflow_id={workflow_id}, url={url}, depth={depth}")
        metrics.counter("autointel_background_started_total", labels={"depth": depth}).inc()

    except Exception as e:
        logger.error(f"Failed to start background /autointel: {e}", exc_info=True)
        metrics.counter("autointel_background_errors_total", labels={"depth": depth}).inc()

        try:
            await interaction.followup.send(
                f"❌ **Failed to Start Analysis**\n\n"
                f"An error occurred while initiating background processing:\n"
                f"```{e!s}```\n\n"
                f"Please try again or contact an administrator.",
                ephemeral=True,
            )
        except Exception:
            # If followup fails, try response (might still be within initial response window)
            with contextlib.suppress(Exception):
                await interaction.response.send_message(f"❌ Error: {e!s}", ephemeral=True)


async def handle_retrieve_results(
    interaction: Interaction,
    background_worker: BackgroundIntelligenceWorker,
    workflow_id: str,
) -> None:
    """Handle /retrieve_results command to fetch completed analysis.

    Args:
        interaction: Discord interaction object
        background_worker: Background task worker
        workflow_id: Workflow ID to retrieve
    """
    try:
        await interaction.response.defer(ephemeral=False)

        # Get workflow status
        status = background_worker.get_workflow_status(workflow_id)

        if not status:
            await interaction.followup.send(
                f"❌ **Workflow Not Found**\n\n"
                f"No workflow found with ID: `{workflow_id}`\n\n"
                f"Possible reasons:\n"
                f"• Invalid workflow ID\n"
                f"• Workflow was cleaned up (results expire after 7 days)\n"
                f"• Workflow was started in a different environment",
                ephemeral=True,
            )
            return

        # Check workflow status
        workflow_status = status.get("status", "unknown")

        if workflow_status == "initiated" or workflow_status == "in_progress":
            # Still running
            progress = status.get("progress", {})
            stage = progress.get("stage", "unknown")
            percentage = progress.get("percentage", 0)
            message = progress.get("message", "Processing...")

            response = (
                f"# ⏳ Analysis In Progress\n\n"
                f"**Workflow ID:** `{workflow_id}`\n"
                f"**Status:** {workflow_status}\n"
                f"**Current Stage:** {stage}\n"
                f"**Progress:** {percentage}%\n"
                f"**Message:** {message}\n\n"
                f"The analysis is still running. Results will be posted here when complete."
            )

            await interaction.followup.send(response)

        elif workflow_status == "completed":
            # Extract and format results
            results = status.get("results", {})
            duration = status.get("duration", 0)

            briefing = "# 🎯 Intelligence Analysis Results (Retrieved)\n\n"
            briefing += f"**Workflow ID:** `{workflow_id}`\n"
            briefing += "**Status:** ✅ Completed\n"
            briefing += f"**Duration:** {duration:.1f}s ({duration / 60:.1f} minutes)\n\n"
            briefing += "---\n\n"

            if results.get("briefing"):
                briefing += results["briefing"]
            elif results.get("raw_output"):
                briefing += f"## Analysis Results\n\n{results['raw_output']}\n\n"
            else:
                briefing += "_No detailed results available._"

            # Split into chunks if needed
            chunks = [briefing[i : i + 1900] for i in range(0, len(briefing), 1900)]

            for chunk in chunks:
                await interaction.followup.send(chunk)

        elif workflow_status == "failed":
            # Error occurred
            error = status.get("error", "Unknown error")

            response = (
                f"# ❌ Analysis Failed\n\n"
                f"**Workflow ID:** `{workflow_id}`\n"
                f"**Status:** Failed\n"
                f"**Error:** {error}\n\n"
                f"Please try running the analysis again or contact an administrator."
            )

            await interaction.followup.send(response)

        else:
            # Unknown status
            await interaction.followup.send(
                f"⚠️ **Unknown Status**\n\n"
                f"Workflow `{workflow_id}` has status: `{workflow_status}`\n\n"
                f"Raw status data:\n```json\n{status}\n```",
                ephemeral=True,
            )

    except Exception as e:
        logger.error(f"Failed to retrieve results: {e}", exc_info=True)

        with contextlib.suppress(Exception):
            await interaction.followup.send(
                f"❌ **Retrieval Error**\n\nFailed to retrieve results for workflow `{workflow_id}`:\n```{e!s}```",
                ephemeral=True,
            )
