"""Discord Progress Updates - Real-time progress reporting utilities.

This module contains Discord progress update logic extracted from discord_helpers.py,
providing utilities to send real-time progress updates with visual progress bars.
"""

from __future__ import annotations

import logging
from typing import Any

from .discord_session_validators import is_session_valid


logger = logging.getLogger(__name__)


async def send_progress_update(
    interaction: Any,
    message: str,
    current: int,
    total: int,
    log: logging.Logger | None = None,
) -> None:
    """Send real-time progress updates to Discord.

    Displays a visual progress bar with emoji indicators and percentage.
    Automatically checks session validity before sending.

    Args:
        interaction: Discord interaction object
        message: Progress message to display
        current: Current step number
        total: Total number of steps
        log: Optional logger instance

    Examples:
        >>> await send_progress_update(interaction, "Downloading media", 2, 5)
        # Output: "Downloading media
        #          🟢🟢⚪⚪⚪ 2/5 (40%)"
    """
    _logger = log or logger

    try:
        # Check if session is still valid before attempting to send
        if not is_session_valid(interaction, _logger):
            _logger.warning(f"Session closed, cannot send progress update: {message}")
            return

        # Prevent division by zero
        if total <= 0:
            total = 1

        progress_bar = "🟢" * current + "⚪" * max(0, total - current)
        progress_percentage = int((current / total) * 100) if total > 0 else 0
        progress_text = f"{message}\n{progress_bar} {current}/{total} ({progress_percentage}%)"

        # Always use followup.send for progress updates since interaction.response.defer() was called
        try:
            await interaction.followup.send(progress_text, ephemeral=False)
        except RuntimeError as e:
            if "Session is closed" in str(e):
                _logger.warning(f"Session closed during progress update: {message}")
            else:
                raise

    except Exception as e:
        # Only log if it's not a session closed error (already handled above)
        if "Session is closed" not in str(e):
            _logger.error(f"Progress update failed: {e}", exc_info=True)
