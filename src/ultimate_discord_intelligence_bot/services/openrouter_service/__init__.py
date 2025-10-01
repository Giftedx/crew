"""OpenRouter service package with modular routing workflow."""

import sys as _sys
import time as _time
from typing import Any

from core.http_utils import is_retry_enabled as _default_is_retry_enabled
from core.http_utils import resilient_post as _default_resilient_post

from .service import OpenRouterService

resilient_post = _default_resilient_post
time = _time
_semantic_cache_get: Any | None = None
is_retry_enabled = _default_is_retry_enabled

__all__ = ["OpenRouterService", "_semantic_cache_get", "resilient_post", "time", "is_retry_enabled"]


def _register_module_aliases() -> None:
    module = _sys.modules[__name__]
    canonical = "ultimate_discord_intelligence_bot.services.openrouter_service"
    alt = "src.ultimate_discord_intelligence_bot.services.openrouter_service"
    if __name__ == canonical:
        _sys.modules.setdefault(alt, module)
    elif __name__ == alt:
        _sys.modules.setdefault(canonical, module)

    for name in (canonical, alt):
        parent_name, _, attr = name.rpartition(".")
        parent = _sys.modules.get(parent_name)
        if parent is not None and not hasattr(parent, attr):
            setattr(parent, attr, module)


_register_module_aliases()
