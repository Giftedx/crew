"""Discord Integration Helpers - Isolated Discord-specific functionality.

This module contains all Discord-specific integration logic extracted from the
autonomous orchestrator, including progress updates, session validation, error
handling, result delivery, and embed creation.

NOTE: This file has been decomposed into focused modules:
- discord_session_validators.py - Discord session validation and management
- discord_progress_updates.py - Real-time progress reporting
- discord_result_persistence.py - Workflow result persistence
- discord_error_handlers.py - Error reporting and handling
- discord_result_delivery.py - Result delivery and presentation
- discord_embed_builders.py - Discord embed creation utilities

This file is maintained for backward compatibility.
"""

from __future__ import annotations

import logging

# ============================================================================
# Backward Compatibility Imports
# ============================================================================
# Import functions from the new focused modules for backward compatibility
from .discord_embed_builders import (
    create_details_embed,
    create_error_embed,
    create_knowledge_base_embed,
    create_main_results_embed,
    create_specialized_details_embed,
    create_specialized_knowledge_embed,
    create_specialized_main_results_embed,
)
from .discord_error_handlers import (
    handle_acquisition_failure,
    send_enhanced_error_response,
    send_error_response,
)
from .discord_progress_updates import (
    send_progress_update,
)
from .discord_result_delivery import (
    deliver_autonomous_results,
)
from .discord_result_persistence import (
    persist_workflow_results,
)
from .discord_session_validators import (
    is_session_valid,
)


logger = logging.getLogger(__name__)

# Export all functions for backward compatibility
__all__ = [
    "create_details_embed",
    "create_error_embed",
    "create_knowledge_base_embed",
    # Embed builders
    "create_main_results_embed",
    "create_specialized_details_embed",
    "create_specialized_knowledge_embed",
    "create_specialized_main_results_embed",
    # Result delivery
    "deliver_autonomous_results",
    # Error handling
    "handle_acquisition_failure",
    # Session validation
    "is_session_valid",
    # Result persistence
    "persist_workflow_results",
    "send_enhanced_error_response",
    "send_error_response",
    # Progress updates
    "send_progress_update",
]
