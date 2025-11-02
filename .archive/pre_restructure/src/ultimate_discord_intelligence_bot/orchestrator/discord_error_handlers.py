"""Discord Error Handling - Error reporting and handling utilities.

This module contains Discord error handling logic extracted from discord_helpers.py,
providing utilities to handle and report errors with user-friendly messages.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from .discord_session_validators import is_session_valid


if TYPE_CHECKING:
    from ultimate_discord_intelligence_bot.step_result import StepResult


logger = logging.getLogger(__name__)


def _get_metrics():
    """Lazy import of metrics to avoid circular dependencies."""
    try:
        from obs.metrics import get_metrics

        return get_metrics()
    except ImportError:
        # Return a no-op metrics object if metrics module not available
        class NoOpMetrics:
            def counter(self, *args, **kwargs):
                pass

            def histogram(self, *args, **kwargs):
                pass

        return NoOpMetrics()


async def handle_acquisition_failure(
    interaction: Any,
    acquisition_result: StepResult,
    url: str,
    log: logging.Logger | None = None,
) -> None:
    """Handle content acquisition failures with specialized guidance.

    Provides user-friendly error messages with actionable guidance based on
    error type (missing dependencies, YouTube protection, etc.).

    Args:
        interaction: Discord interaction object
        acquisition_result: Failed acquisition StepResult
        url: URL that failed to be acquired
        log: Optional logger instance
    """
    _logger = log or logger

    try:
        error_data = acquisition_result.data or {}
        error_type = error_data.get("error_type", "general")

        # Recognize missing dependency surfaced by YtDlpDownloadTool
        if error_type == "dependency_missing" or (
            isinstance(acquisition_result.error, str) and "yt-dlp" in acquisition_result.error.lower()
        ):
            guidance = error_data.get(
                "guidance",
                (
                    "yt-dlp is missing on this system. Install it with 'pip install yt-dlp' or run 'make first-run' "
                    "to set up the environment. You can also run 'make doctor' to verify binaries."
                ),
            )
            enhanced_error = (
                "🔧 Missing Dependency Detected: yt-dlp\n\n"
                "The downloader requires yt-dlp to fetch media.\n\n"
                f"Guidance: {guidance}"
            )
            await send_enhanced_error_response(interaction, "Content Acquisition", enhanced_error, _logger)
            return

        if error_type == "youtube_protection":
            enhanced_error = (
                "🎬 **YouTube Download Issue Detected**\n\n"
                "The video appears to have YouTube's enhanced protection enabled. This is common for:\n"
                "• Popular or trending videos\n"
                "• Videos with restricted access\n"
                "• Content with digital rights management\n\n"
                "**Suggestions:**\n"
                "• Try a different YouTube video\n"
                "• Use a direct video file URL instead\n"
                "• The autonomous system attempted multiple quality fallbacks but YouTube blocked all formats\n\n"
                f"**Technical Details:** {acquisition_result.error or 'Unknown error'}..."
            )
            await send_enhanced_error_response(interaction, "Content Acquisition", enhanced_error, _logger)
        else:
            # General acquisition failure
            error_msg = acquisition_result.error or "Content acquisition failed"
            await send_error_response(interaction, "Content Acquisition", error_msg, _logger)

    except Exception as e:
        # Fallback error handling
        await send_error_response(
            interaction,
            "Content Acquisition",
            f"Failed to acquire content from {url}: {e}",
            _logger,
        )


async def send_error_response(
    interaction: Any,
    stage: str,
    error: str,
    log: logging.Logger | None = None,
) -> None:
    """Send error response to Discord with session resilience.

    Args:
        interaction: Discord interaction object
        stage: Stage name where error occurred
        error: Error message to send
        log: Optional logger instance

    Note:
        If session is closed, error is logged instead of sent.
        This prevents cascading RuntimeError exceptions.
    """
    _logger = log or logger

    try:
        # Check if session is still valid
        if not is_session_valid(interaction, _logger):
            _logger.error(f"❌ Session closed, cannot send error response to Discord.\nStage: {stage}\nError: {error}")
            # Track metric for session closure during error handling
            _get_metrics().counter(
                "discord_session_closed_total",
                labels={"stage": f"error_response_{stage.lower().replace(' ', '_')}"},
            )
            return

        # Import here to avoid circular dependency
        from .discord_embed_builders import create_error_embed

        error_embed = await create_error_embed(stage, error)
        try:
            await interaction.followup.send(embed=error_embed, ephemeral=False)
        except RuntimeError as e:
            if "Session is closed" in str(e):
                _logger.error(f"❌ Session closed while sending error embed.\nStage: {stage}\nError: {error}")
                # Track metric
                _get_metrics().counter(
                    "discord_session_closed_total",
                    labels={"stage": f"error_response_send_{stage.lower().replace(' ', '_')}"},
                )
                return
            else:
                raise
    except Exception as e:
        # Don't log session closed errors (already handled)
        if "Session is closed" in str(e):
            _logger.error(f"Session closed during error response for {stage}: {error}")
            return

        # Fallback to text response for other errors
        try:
            if is_session_valid(interaction, _logger):
                await interaction.followup.send(
                    f"❌ Autonomous Intelligence Error\n"
                    f"**Stage:** {stage}\n"
                    f"**Error:** {error}\n\n"
                    f"The autonomous workflow encountered an issue during processing.",
                    ephemeral=False,
                )
            else:
                _logger.error(f"Session closed during error fallback for {stage}: {error}")
        except Exception as fallback_error:
            if "Session is closed" not in str(fallback_error):
                _logger.error(f"All error reporting failed for {stage}: {error}")


async def send_enhanced_error_response(
    interaction: Any,
    stage: str,
    enhanced_message: str,
    log: logging.Logger | None = None,
) -> None:
    """Send enhanced user-friendly error response to Discord.

    Args:
        interaction: Discord interaction object
        stage: Stage name where error occurred
        enhanced_message: Pre-formatted error message with guidance
        log: Optional logger instance
    """
    _logger = log or logger

    try:
        await interaction.followup.send(
            f"❌ **Autonomous Intelligence - {stage}**\n\n{enhanced_message}",
            ephemeral=False,
        )
    except Exception:
        # Fallback to basic error response
        await send_error_response(interaction, stage, "Enhanced error details unavailable", _logger)
