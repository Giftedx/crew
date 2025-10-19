"""Discord Session Validation - Session management and validation utilities.

This module contains Discord session validation logic extracted from discord_helpers.py,
providing utilities to check if Discord interactions are still valid for sending messages.
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


def is_session_valid(interaction: Any, log: logging.Logger | None = None) -> bool:
    """Check if Discord session is still valid for sending messages.

    Args:
        interaction: Discord interaction object
        log: Optional logger instance (defaults to module logger)

    Returns:
        True if session is valid and can receive messages
        False if session is closed or invalid

    Examples:
        >>> if is_session_valid(interaction):
        ...     await send_progress_update(interaction, "Processing...", 1, 5)
    """
    _logger = log or logger

    try:
        # Check if interaction has a webhook and if the session is open
        if not hasattr(interaction, "followup"):
            _logger.debug("Interaction missing 'followup' attribute")
            return False

        # Check if the underlying webhook has a valid session
        if hasattr(interaction.followup, "_adapter"):
            adapter = interaction.followup._adapter
            if hasattr(adapter, "_session") and adapter._session:
                session = adapter._session
                # aiohttp session has a 'closed' property
                if hasattr(session, "closed"):
                    is_open = not session.closed
                    if not is_open:
                        _logger.warning("Discord aiohttp session detected as closed")
                    return is_open

        # Additional validation: try to access interaction properties
        try:
            _ = interaction.id  # Will fail if interaction is invalid
        except Exception as e:
            _logger.debug(f"Interaction ID access failed: {e}")
            return False

        # If we can't determine session state definitively, assume it might work
        return True
    except Exception as e:
        # If any check fails, assume session is invalid
        _logger.debug(f"Session validation failed with exception: {e}")
        return False
