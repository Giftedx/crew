"""Knowledge layer for unified content retrieval and search.

This module provides high-level APIs for querying across platforms,
social graph mapping, and cross-platform content discovery.
"""

from __future__ import annotations

from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from .api import KnowledgeAPI

# Optional import for ML-dependent features
# Catch all exceptions (not just ImportError) because ML dependencies may have broken dependency chains
try:
    from .api import KnowledgeAPI
except Exception:
    # Graceful fallback when ML dependencies unavailable
    KnowledgeAPI = None  # type: ignore[assignment,misc]

from .retrieval import ContentRetriever
from .social_graph import SocialGraphMapper


__all__ = [
    "ContentRetriever",
    "KnowledgeAPI",
    "SocialGraphMapper",
]
