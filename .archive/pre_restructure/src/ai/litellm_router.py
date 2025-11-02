"""LiteLLM router singleton and helpers.

Creates a global LiteLLM Router configured from SecureConfig with optional
Redis cache, fallback routing, and budget controls. This module does not change
existing behavior unless ENABLE_LITELLM_ROUTER=true.
"""

from __future__ import annotations

import logging
from typing import Any, ClassVar

from core.secure_config import get_config


try:
    from litellm import Router as _Router  # type: ignore[import-not-found]

    LITELLM_AVAILABLE: bool = True
except Exception:  # pragma: no cover - optional dependency
    _Router = None  # type: ignore[assignment]
    LITELLM_AVAILABLE = False

logger = logging.getLogger(__name__)


class LLMRouterSingleton:
    """Singleton factory for LiteLLM Router.

    Use `get()` to retrieve a configured Router instance or `None` if disabled.
    """

    _instance: ClassVar[Any | None] = None

    @classmethod
    def is_enabled(cls) -> bool:
        cfg = get_config()
        return bool(getattr(cfg, "enable_litellm_router", False) and LITELLM_AVAILABLE)

    @classmethod
    def get(cls) -> Any | None:
        """Return a configured LiteLLM Router or None if disabled/unavailable."""
        if not cls.is_enabled():
            if LITELLM_AVAILABLE:
                logger.debug("LiteLLM router disabled via feature flag")
            else:
                logger.debug("LiteLLM not installed; router unavailable")
            return None

        if cls._instance is not None:
            return cls._instance

        cfg = get_config()
        try:
            # Minimal model list - allow OpenRouter "model" passthrough
            model_list = [
                {
                    "model_name": getattr(cfg, "openrouter_general_model", None)
                    or getattr(cfg, "openrouter_analysis_model", None)
                    or "openai/gpt-4o-mini",
                    "litellm_params": {
                        "api_key": getattr(cfg, "openrouter_api_key", None) or getattr(cfg, "openai_api_key", None),
                        "api_base": "https://openrouter.ai/api/v1",
                    },
                }
            ]

            router = _Router(  # type: ignore[misc]
                model_list=model_list,
                routing_strategy=getattr(cfg, "litellm_routing_strategy", "usage-based-routing"),
                cache=getattr(cfg, "litellm_cache_enabled", True),
                fallbacks_enabled=getattr(cfg, "litellm_fallback_enabled", True),
            )

            cls._instance = router
            logger.info(
                "LiteLLM router initialised (strategy=%s)",
                getattr(cfg, "litellm_routing_strategy", "usage-based-routing"),
            )
            return cls._instance
        except Exception as exc:  # pragma: no cover - defensive guard
            logger.warning("Failed to initialise LiteLLM router: %s", exc)
            cls._instance = None
            return None


__all__ = ["LITELLM_AVAILABLE", "LLMRouterSingleton"]
